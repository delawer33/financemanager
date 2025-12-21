from datetime import timedelta
import pandas as pd
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.db.models import CharField
from django.db.models.functions import Cast
from transaction.models import Category


def period_stats(qs):
    total_income = qs.filter(
        type='INCOME',
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_expense = qs.filter(
        type='OUTCOME',
    ).aggregate(total=Sum('amount'))['total'] or 0

    balance = total_income - total_expense
    
    transactions = qs.annotate(
        day=Cast(TruncDate('date'), CharField())
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

    expense_categories_raw = qs.filter(
        type='OUTCOME',
    ).values('category__name', 'category__id').annotate(total=Sum('amount'))
    
    # Обрабатываем переводы для категорий
    expense_categories = []
    for item in expense_categories_raw:
        category_name = item['category__name']
        if category_name and item['category__id']:
            try:
                category = Category.objects.get(id=item['category__id'])
                translated_name = category.translated_name
            except Category.DoesNotExist:
                translated_name = category_name
        else:
            translated_name = category_name or 'Other'
        
        expense_categories.append({
            'category__name': translated_name,
            'total': item['total']
        })

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
    qs = qs.filter(type="OUTCOME").values('category__name', 'category__id').annotate(count=Count('id'))
    expense_frequency_categories = []
    expense_frequency_values = []

    for t in qs:
        if t['category__name'] and t['category__id']:
            try:
                category = Category.objects.get(id=t['category__id'])
                translated_name = category.translated_name
            except Category.DoesNotExist:
                translated_name = t['category__name']
            expense_frequency_categories.append(translated_name)
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
    hm_data = qs.filter(type="OUTCOME").order_by('date').values('date', 'amount')
    
    data_list = [
        {
            'date': item['date'],
            'amount': float(item['amount'])
        }
        for item in hm_data
    ]

    if data_list:
        df = pd.DataFrame(data_list)
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
    qs = qs.select_related('category', 'account', 'user')
    
    data = period_stats(qs)
    data.update(get_data_for_heatmap(qs))
    data.update(expense_frequency_data(qs))
    return data
