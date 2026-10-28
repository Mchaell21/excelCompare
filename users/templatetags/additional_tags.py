from django import template

register = template.Library()
def _resolve_part(value, part):
    if isinstance(value, dict):
        if part in value:
            return value[part]
        return None
    try:
        return getattr(value, part)
    except (AttributeError, TypeError):
        pass
    try:
        return value[int(part)]
    except (TypeError, ValueError, IndexError, KeyError):
        return None


@register.filter
def get_item(value, key):
    if value is None or not key:
        return ''
    current = value
    for part in str(key).split('.'):
        current = _resolve_part(current, part)
        if current is None:
            return ''
    return current


@register.filter
def display_status(value):
    if not value:
        return ''
    return str(value).capitalize()


class TableColumnsNode(template.Node):
    def __init__(self, nodelist, asvar):
        self.nodelist = nodelist
        self.asvar = asvar

    def render(self, context):
        columns = []
        context['__table_columns__'] = columns
        try:
            self.nodelist.render(context)
        finally:
            if '__table_columns__' in context:
                del context['__table_columns__']
        if self.asvar:
            context[self.asvar] = columns
        return ''


@register.tag(name='table_columns')
def do_table_columns(parser, token):
    bits = token.split_contents()
    if len(bits) != 3 or bits[1] != 'as':
        raise template.TemplateSyntaxError(
            "'table_columns' syntax: "
            "{% table_columns as VAR %} ... {% endtable_columns %}")
    nodelist = parser.parse(('endtable_columns',))
    parser.delete_first_token()
    return TableColumnsNode(nodelist, bits[2])


class TableColumnNode(template.Node):
    def __init__(self, kwargs):
        self.kwargs = kwargs

    def render(self, context):
        target = context.get('__table_columns__')
        if target is None:
            raise template.TemplateSyntaxError(
                "'column' hanya boleh dipakai di dalam {% table_columns %}.")
        col = {}
        for name, fexpr in self.kwargs.items():
            value = fexpr.resolve(context)
            # Dukung penulisan flag: hide_mobile="true" / card_action="1"
            if isinstance(value, str) and value.lower() in ('1', 'true', 'yes', 'on'):
                value = True
            col[name] = value
        target.append(col)
        return ''


@register.tag(name='column')
def do_column(parser, token):
    bits = token.split_contents()
    tagname = bits.pop(0)
    if not bits:
        raise template.TemplateSyntaxError(
            f"'{tagname}' butuh minimal satu argumen keyword (label=...).")
    kwargs = {}
    for bit in bits:
        if '=' not in bit:
            raise template.TemplateSyntaxError(
                f"'{tagname}' hanya menerima argumen keyword.")
        name, raw = bit.split('=', 1)
        kwargs[name] = parser.compile_filter(raw)
    return TableColumnNode(kwargs)
