# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#
__author__ = """Johannes Raggam <johannes@raggam.co.at>"""
__docformat__ = 'plaintext'

import logging
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import normalizeString
from Products.ATContentTypes.lib import constraintypes
from Products.PortalTransforms.Transform import make_config_persistent
from Products.CMFCore.WorkflowCore import WorkflowException

import os
from App.Common import package_home

class SetupHandlerTools(object):

    def __init__(self, context,
                 packagename='collective.setuphandlertools',
                 package_globals=None):
        self.context = context
        self.packagename = packagename
        self.package_globals = package_globals
        self.logger = logging.getLogger(self.packagename)


    def isNotThisProfile(self, marker_file):
        return self.context.readDataFile(marker_file) is None


    def load_file(self, name, subdir=None):
        """Load a file from data directory."""
        PACKAGE_HOME = package_home(self.package_globals)
        if subdir:
            path = os.path.join(PACKAGE_HOME, subdir, name)
        else:
            path = os.path.join(PACKAGE_HOME, name)
        file_desc = open(path, 'rb')
        data = file_desc.read()
        file_desc.close()
        return data


    def unsafe_html_transform(self):
        tid = 'safe_html'

        tconfig = dict()
        tconfig['class_blacklist'] = []
        tconfig['nasty_tags'] = {'meta': '1'}
        tconfig['remove_javascript'] = 0
        tconfig['stripped_attributes'] = ['lang', 'valign', 'halign', 'border',
                                         'frame', 'rules', 'cellspacing',
                                         'cellpadding', 'bgcolor']
        tconfig['stripped_combinations'] = {}
        tconfig['style_whitelist'] = ['text-align', 'list-style-type', 'float',
                                      'width', 'height', 'padding-left',
                                      'padding-right'] # allow specific styles for
                                                       # TinyMCE editing
        tconfig['valid_tags'] = {
            'code': '1', 'meter': '1', 'tbody': '1', 'style': '1', 'img': '0',
            'title': '1', 'tt': '1', 'tr': '1', 'param': '1', 'li': '1',
            'source': '1', 'tfoot': '1', 'th': '1', 'td': '1', 'dl': '1',
            'blockquote': '1', 'big': '1', 'dd': '1', 'kbd': '1', 'dt': '1',
            'p': '1', 'small': '1', 'output': '1', 'div': '1', 'em': '1',
            'datalist': '1', 'hgroup': '1', 'video': '1', 'rt': '1', 'canvas': '1',
            'rp': '1', 'sub': '1', 'bdo': '1', 'sup': '1', 'progress': '1',
            'body': '1', 'acronym': '1', 'base': '0', 'br': '0', 'address': '1',
            'article': '1', 'strong': '1', 'ol': '1', 'script': '1', 'caption': '1',
            'dialog': '1', 'col': '1', 'h2': '1', 'h3': '1', 'h1': '1', 'h6': '1',
            'h4': '1', 'h5': '1', 'header': '1', 'table': '1', 'span': '1',
            'area': '0', 'mark': '1', 'dfn': '1', 'var': '1', 'cite': '1',
            'thead': '1', 'head': '1', 'hr': '0', 'link': '1', 'ruby': '1',
            'b': '1', 'colgroup': '1', 'keygen': '1', 'ul': '1', 'del': '1',
            'iframe': '1', 'embed': '1', 'pre': '1', 'figure': '1', 'ins': '1',
            'aside': '1', 'html': '1', 'nav': '1', 'details': '1', 'u': '1',
            'samp': '1', 'map': '1', 'object': '1', 'a': '1', 'footer': '1',
            'i': '1', 'q': '1', 'command': '1', 'time': '1', 'audio': '1',
            'section': '1', 'abbr': '1'}

        self.setup_portal_transforms(tid, tconfig)


    def setup_portal_transforms(self, transform_id, transform_config):
        self.logger.info('Updating portal_transform settings from' + transform_id)

        pt = getToolByName(self.context, 'portal_transforms')
        if not transform_id in pt.objectIds(): return
        trans = pt[transform_id]

        tconfig = trans._config
        tconfig.update(transform_config)

        make_config_persistent(tconfig)
        trans._p_changed = True
        trans.reload()

    """
    [{'type':None,
      'id':None,
      'title':None,
      'data':{},
      'childs':[],
      'opts':{
          'lang':None,
          'setDefault':None,
          'setExcludeFromNav':None,
          'setLayout':None,
          'setLocallyAllowedTypes':None,
          'setImmediatelyAddableTypes':None,
          'workflow':None,}
      }
     ]
     """
    def create_item(self, ctx, id, item):
        if not id in ctx.contentIds():
            wft = getToolByName(ctx, 'portal_workflow')
            ctx.invokeFactory(item['type'], id, title=item['title'], **item['data'])
            if 'setExcludeFromNav' in item['opts']:
                ctx[id].setExcludeFromNav(item['opts']['setExcludeFromNav'])
            if 'setLayout' in item['opts']:
                ctx[id].setLayout(item['opts']['setLayout'])
            if 'setLocallyAllowedTypes' in item['opts']:
                try:
                    ctx[id].setConstrainTypesMode(constraintypes.ENABLED)
                    ctx[id].setLocallyAllowedTypes(item['opts']['setLocallyAllowedTypes'])
                except: pass # not a folder?
            if 'setImmediatelyAddableTypes' in item['opts']:
                try:
                    ctx[id].setConstrainTypesMode(constraintypes.ENABLED)
                    ctx[id].setImmediatelyAddableTypes(item['opts']['setImmediatelyAddableTypes'])
                except: pass # not a folder?
            if 'workflow' in item['opts']:
                if item['opts']['workflow'] is not None: # else leave it in original state
                    wft.doActionFor(ctx[id], item['opts']['workflow'])
            else:
                try:
                    wft.doActionFor(ctx[id], 'publish')
                except WorkflowException:
                    pass # e.g. "No workflows found"
            ctx[id].setLanguage(item['opts']['lang'])
            ctx[id].reindexObject()
            self.logger.info('added %s' % id)


    def create_item_runner(self, ctx, content, lang='en'):
        for item in content:
            if 'id' not in item:
                id = normalizeString(item['title'], context=ctx)
            else:
                id = item['id']
            if not id in ctx.contentIds():
                if 'opts' not in item or not item['opts']:
                    item['opts'] = {}
                if 'data' not in item or not item['data']:
                    item['data'] = {}
                if 'lang' not in item['opts']:
                    item['opts']['lang'] = lang
                self.create_item(ctx, id, item)
                if 'setDefault' in item['opts']:
                    ctx.setDefaultPage(id)
            if 'childs' in item and item['childs']:
                self.create_item_runner(ctx[id], item['childs'], lang=lang)


    def add_calendar_type(self, calendar_types):
        """ Configures Products.CMFPlone.CalendarTool
        """
        calendar_tool = getToolByName(self.context, 'portal_calendar')
        if isinstance(list, calendar_types):
            calendar_types = tuple(calendar_types)
        if not isinstance(tuple, calendar_types):
            calendar_types = (calendar_types, )
        calendar_tool.calendar_types += calendar_types
        self.logger.info('added %s to calendar_types' % str(calendar_types))