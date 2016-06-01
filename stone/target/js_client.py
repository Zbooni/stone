from __future__ import absolute_import, division, print_function, unicode_literals

import argparse

from stone.data_type import (
    is_user_defined_type,
    unwrap,
)
from stone.generator import CodeGenerator
from stone.target.js_helpers import (
    fmt_func,
    fmt_obj,
    fmt_type,
)


_cmdline_parser = argparse.ArgumentParser(prog='js-client-generator')
_cmdline_parser.add_argument(
    'filename',
    help=('The name to give the single Javascript file that is created and '
          'contains all of the routes.'),
)
_cmdline_parser.add_argument(
    '-a',
    '--route-attribute',
    action='append',
    type=str,
    default=[],
    help='Route attribute to include in the invocation of this.request.',
)

_header = """\
// Auto-generated by Stone, do not modify.
/**
 * @class Routes
 * @classdesc Contains a corresponding method for each route.
 */
var routes = {};
"""


class JavascriptGenerator(CodeGenerator):
    """Generates a single Javascript file with all of the routes defined."""

    cmdline_parser = _cmdline_parser

    # Instance var of the current namespace being generated
    cur_namespace = None

    preserve_aliases = True

    def generate(self, api):
        with self.output_to_relative_path(self.args.filename):

            self.emit_raw(_header)

            for namespace in api.namespaces.values():
                for route in namespace.routes:
                    self._generate_route(namespace, route)

            self.emit()
            self.emit('module.exports = routes;')

    def _generate_route(self, namespace, route):
        function_name = fmt_func(namespace.name + '_' + route.name)
        self.emit()
        self.emit('/**')
        if route.doc:
            self.emit_wrapped_text(self.process_doc(route.doc, self._docf), prefix=' * ')
        self.emit(' * @function Routes#%s' % function_name)
        if route.deprecated:
            self.emit(' * @deprecated')

        self.emit(' * @arg {%s} arg - The request parameters.' %
                  fmt_type(route.arg_data_type))
        if is_user_defined_type(route.arg_data_type):
            for field in route.arg_data_type.all_fields:
                field_doc = ' - ' + field.doc if field.doc else ''
                field_type, nullable, _ = unwrap(field.data_type)
                field_js_type = fmt_type(field_type)
                if nullable:
                    field_js_type += '|null'
                self.emit_wrapped_text(
                    '@arg {%s} arg.%s%s' %
                        (field_js_type, field.name,
                         self.process_doc(field_doc, self._docf)),
                    prefix=' * ')
        self.emit(' * @returns {%s}' % fmt_type(route.result_data_type))
        self.emit(' */')
        self.emit('routes.%s = function (arg) {' % function_name)
        with self.indent(dent=2):
            url = '{}/{}'.format(namespace.name, route.name)
            if self.args.route_attribute:
                additional_args = []
                for attr in self.args.route_attribute:
                    additional_args.append(fmt_obj(route.attrs.get(attr)))
                self.emit(
                    "return this.request('{}', arg, {});".format(
                        url, ', '.join(additional_args)))
            else:
                self.emit(
                    'return this.request("%s", arg);' % url)
        self.emit('};')

    def _docf(self, tag, val):
        """
        Callback used as the handler argument to process_docs(). This converts
        Stone doc references to JSDoc-friendly annotations.
        """
        # TODO(kelkabany): We're currently just dropping all doc ref tags.
        return val
