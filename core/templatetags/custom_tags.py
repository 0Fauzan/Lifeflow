from django import template
register = template.Library()

@register.filter
def urgency_class(urgency):
    return {
        'critical': 'urg-critical',
        'high':     'urg-high',
        'medium':   'urg-medium',
        'low':      'urg-low',
    }.get(urgency, '')

@register.filter
def status_class(status):
    return {
        'pending':   'pending',
        'approved':  'approved',
        'fulfilled': 'fulfilled',
        'rejected':  'rejected',
        'cancelled': 'cancelled',
        'upcoming':  'upcoming',
        'ongoing':   'ongoing',
        'completed': 'completed',
    }.get(status, '')

@register.filter
def stock_class(status):
    return {
        'Adequate':     'adequate',
        'Low':          'low',
        'Critical':     'critical',
        'Out of Stock': 'empty',
    }.get(status, 'empty')
