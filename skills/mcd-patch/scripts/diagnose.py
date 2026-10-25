#!/usr/bin/env python3
"""Diagnose a bounded set of fully quoted carts; all money is integer cents."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def integer(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(f'{label} 必须是非负整数分')
    return value


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} 必须是非空文本')
    return value


def timestamp(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('时间必须含时区')
    return dt


def diagnose(data, *, allow_demo=False, now=None, max_age_seconds=300):
    if data.get('schema_version') != 1 or data.get('mode') not in ('demo', 'live'):
        raise ValueError('需要 schema_version=1 和 mode=demo/live')
    if data['mode'] == 'demo' and not allow_demo:
        raise ValueError('演示数据需要显式 --demo，不能冒充真实核价')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or max_age_seconds <= 0:
        raise ValueError('当前时间必须含时区，新鲜度窗口必须为正')
    budget = integer(data['budget_cents'], 'budget_cents')
    context = data['context']
    for key in ('store_id', 'dining_mode'):
        nonempty(context.get(key), key)
    if context.get('currency') != 'CNY':
        raise ValueError('仅支持人民币 CNY')
    constraints = {}
    for condition in data['constraints']:
        key = nonempty(condition.get('id'), 'condition id')
        if key in constraints or type(condition.get('relaxable')) is not bool:
            raise ValueError('条件 ID 不能重复，relaxable 必须是布尔值')
        nonempty(condition.get('label'), 'condition label')
        constraints[key] = condition
    if not constraints:
        raise ValueError('至少需要一项需求条件')
    accepted, changes, excluded, seen = [], [], [], set()
    for cart in data['candidates']:
        key = nonempty(cart.get('id'), 'candidate id')
        if key in seen:
            raise ValueError('候选 ID 不能重复')
        seen.add(key)
        nonempty(cart.get('label'), 'candidate label')
        nonempty(cart.get('allocation'), 'allocation')
        reasons = []
        if cart.get('context') != context:
            reasons.append('门店/就餐方式/币种上下文不一致')
        quote = cart.get('quote') or {}
        try:
            price = integer(quote.get('total_cents'), 'total_cents')
            nonempty(quote.get('evidence'), 'quote evidence')
            if quote.get('source') != 'calculate-price':
                raise ValueError('缺少官方完整购物车核价来源')
            age = (now - timestamp(quote['observed_at'])).total_seconds()
            if not -30 <= age <= max_age_seconds:
                raise ValueError('报价过期或时间异常，需要重新核价')
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            reasons.append('核价无效：' + str(exc))
            price = None
        checks = cart.get('checks', {})
        if not isinstance(checks, dict) or set(checks) - set(constraints):
            raise ValueError('checks 必须是对象，且不能含未定义的条件 ID')
        failed = []
        for cid, condition in constraints.items():
            check = checks.get(cid) or {}
            status = check.get('status', 'unknown')
            if status not in ('pass', 'fail', 'unknown'):
                raise ValueError('检查状态只能是 pass/fail/unknown')
            evidence = check.get('evidence')
            if not isinstance(evidence, str) or not evidence.strip() or status == 'unknown':
                reasons.append('待核实：' + condition['label'])
            elif status == 'fail':
                if condition['relaxable']:
                    failed.append(cid)
                else:
                    reasons.append('未满足不可调整条件：' + condition['label'])
        if reasons:
            excluded.append({'id': key, 'reasons': reasons})
            continue
        summary = {
            'id': key, 'label': cart['label'], 'allocation': cart['allocation'],
            'total_cents': price, 'quoted_at': quote['observed_at'],
            'evidence': quote['evidence'],
        }
        if not failed and price <= budget:
            accepted.append(summary)
        else:
            changes.append({**summary, 'relax': sorted(failed),
                            'budget_increase_cents': max(0, price - budget)})
    # A patch dominates another only if it relaxes a subset of conditions and
    # needs no more money; cardinality alone loses distinct user preferences.
    changes.sort(key=lambda x: (len(x['relax']), x['budget_increase_cents'],
                                x['total_cents'], x['id']))
    frontier = []
    for proposal in changes:
        if any(set(other['relax']) <= set(proposal['relax']) and
               other['budget_increase_cents'] <= proposal['budget_increase_cents']
               for other in frontier):
            continue
        frontier.append(proposal)
    accepted.sort(key=lambda x: (x['total_cents'], x['id']))
    status = ('feasible' if accepted else 'needs_change' if frontier else
              'insufficient_data' if excluded else 'no_candidate')
    return {
        'mode': data['mode'], 'status': status,
        'scope': '仅限本次提交且有效核价的候选，不代表全菜单最优',
        'budget_cents': budget, 'evaluated_count': len(seen),
        'feasible': accepted, 'patches': [] if accepted else frontier,
        'excluded': excluded,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--max-age-seconds', type=int, default=300)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding='utf-8'))
        # Fixed-time replay is only available for explicitly labelled demos.
        now = timestamp(data['demo_now']) if args.demo and data.get('mode') == 'demo' else None
        result = diagnose(data, allow_demo=args.demo, now=now,
                          max_age_seconds=args.max_age_seconds)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print('输入无法诊断：' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
