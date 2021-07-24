from django import template

register = template.Library()

@register.filter(name='int_range')
def int_range(value):
  return range(int(value))