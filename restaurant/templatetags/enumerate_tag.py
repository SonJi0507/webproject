from django import template

register = template.Library()

@register.filter(name='enumerate_')
def enumerate_(value):
  return enumerate(value)