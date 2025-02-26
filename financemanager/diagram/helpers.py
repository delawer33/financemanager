import pandas as pd
from django.db.models import Sum

from transaction.models import Transaction


def period_stats(qs):
    total_income = qs.filter(
        type='INCOME',
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_expense = qs.filter(
        type='OUTCOME',
    ).aggregate(total=Sum('amount'))['total'] or 0

    balance = total_income - total_expense

    transactions = qs.extra(
        select={'day': "strftime('%%Y-%%m-%%d', date)"}
    ).values('day', 'type').annotate(total=Sum('amount'))

    labels = sorted(set(t['day'] for t in transactions))

    income_data = [0] * len(labels)
    expense_data = [0] * len(labels)

    for t in transactions:
        index = labels.index(t['day'])
        if t['type'] == 'INCOME':
            income_data[index] = float(t['total'])
        elif t['type'] == 'OUTCOME':
            expense_data[index] = float(t['total'])

    expense_categories = qs.filter(
        type='OUTCOME',
    ).values('category__name').annotate(total=Sum('amount'))

    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'labels': labels,
        'income_data': income_data,
        'expense_data': expense_data,
        'expense_categories': expense_categories
    }


def weekday_to_number(weekday):
    match weekday:
        case "Monday":
            return 0
        case "Tuesday":
            return 1
        case "Wednesday":
            return 2
        case "Thursday":
            return 3
        case "Friday":
            return 4
        case "Saturday":
            return 5
        case "Sunday":
            return 6


def extended_period_stats(qs):
    data = period_stats(qs)
    expense_heatmap = []
    hm_qs = qs.order_by('date').filter(type="OUTCOME")
    hm_data = [
        {
            'date': t.date,
            'amount': float(t.amount)
        }
        for t in hm_qs
    ]
    df = pd.DataFrame(hm_data)
    df['weekday'] = pd.to_datetime(df['date']).dt.day_name()
    df['week'] = pd.to_datetime(df['date']).dt.isocalendar().week

    heatmap_data = df.groupby(['weekday', 'week'])['amount'].sum().reset_index()

    print(heatmap_data)

    heatmap_data['weekday_num'] = heatmap_data['weekday'].map(weekday_to_number)
    heatmap_data = heatmap_data.sort_values(by=['week', 'weekday_num'])

    weeks_names_for_heatmap = list(map(int, heatmap_data['week'].unique()))
    print(weeks_names_for_heatmap)

    print(heatmap_data)
    heatmap_list = [
        {
            'x': row['weekday'],
            'y': f"{row['week']}",
            'heat': row['amount']
        }
        for _, row in heatmap_data.iterrows()
    ]

    data['heatmap'] = heatmap_list
    data['weeks_names_for_heatmap'] = weeks_names_for_heatmap
    data['day_names_for_heatmap'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    # print(df)
    return data
