from datetime import timedelta
import pandas as pd
from django.db.models import Sum, Count


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


def expense_frequency_data(qs):
    qs = qs.filter(type="OUTCOME").values('category__name').annotate(count=Count('id'))
    expense_frequency_categories = []
    expense_frequency_values = []

    for t in qs:
        if t['category__name']:
            expense_frequency_categories.append(t['category__name'])
        else:
            expense_frequency_categories.append('Other')

        expense_frequency_values.append(t['count'])
    
    return {
        'expense_frequency_categories': expense_frequency_categories,
        'expense_frequency_values': expense_frequency_values
    }


def get_data_for_heatmap(qs):
    heatmap_list = []
    weeks_names_for_heatmap = []
    hm_qs = qs.order_by('date').filter(type="OUTCOME")
    hm_data = [
        {
            'date': t.date,
            'amount': float(t.amount)
        }
        for t in hm_qs
    ]

    if hm_data:
        df = pd.DataFrame(hm_data)
        df['weekday'] = pd.to_datetime(df['date']).dt.day_name()
        df['week'] = pd.to_datetime(df['date']).dt.isocalendar().week
        df['year'] = pd.to_datetime(df['date']).dt.isocalendar().year
        heatmap_data = df.groupby(['year', 'week', 'weekday'])['amount'].sum().reset_index()

        heatmap_data['weekday_num'] = heatmap_data['weekday'].map(weekday_to_number)
        heatmap_data = heatmap_data.sort_values(by=['year', 'week', 'weekday_num'])

        heatmap_data['monday_date'] = pd.to_datetime(
            heatmap_data['year'].astype(str) + '-' + 
            heatmap_data['week'].astype(str) + '-1', 
            format='%Y-%W-%w'
        )
        heatmap_data['sunday_date'] = heatmap_data['monday_date'] + timedelta(days=6)

        heatmap_data['week_label'] = heatmap_data.apply(
            lambda row: 
            f"{row['monday_date'].day}{row['monday_date'].month_name()[:3]}" + \
            f"-{row['sunday_date'].day}{row['sunday_date'].month_name()[:3]}",
            axis=1
        )

        weeks_names_for_heatmap = heatmap_data[['week', 'week_label']].drop_duplicates()
        weeks_names_for_heatmap = weeks_names_for_heatmap['week_label'].to_list()

        heatmap_list = [
            {
                'x': row['weekday'],
                'y': f"{row['week_label']}",
                'heat': row['amount']
            }
            for _, row in heatmap_data.iterrows()
        ]
    return {
        'heatmap': heatmap_list,
        'weeks_names_for_heatmap': weeks_names_for_heatmap,
        'day_names_for_heatmap': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    }


def extended_period_stats(qs):
    data = period_stats(qs)
    data.update(get_data_for_heatmap(qs))
    data.update(expense_frequency_data(qs))

    return data
