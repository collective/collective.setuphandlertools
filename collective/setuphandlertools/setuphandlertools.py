import logging
import os
import sys
from Products.ATContentTypes.lib import constraintypes
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.utils import normalizeString
from Products.PortalTransforms.Transform import make_config_persistent

logger = logging.getLogger('collective.setuphandlertools')


def add_calendar_type(context, calendar_types, logger=logger):
    """ Adds calendar types to Products.CMFPlone.CalendarTool.

    @param context: A Plone context.

    @param calendar_types: Tuple of names of calendar types to be added to
                           portal_calendar.

    @param logger: (Optional) A logging instance.

    """
    calendar_tool = getToolByName(context, 'portal_calendar')
    if isinstance(list, calendar_types):
        calendar_types = tuple(calendar_types)
    if not isinstance(tuple, calendar_types):
        calendar_types = (calendar_types, )
    calendar_tool.calendar_types += calendar_types
    logger.info('added %s to calendar_types' % str(calendar_types))


def add_group(context, name, roles=None, groups=None, members=None,
              logger=logger):
    """ Add a group to plone.

    @param context: A Plone context.

    @param name: The name of the group to add.

    @param roles: A list of roles, the group should be in.

    @param groups: A list of groups, the group should be in.

    @param members: A list of member ids to add to the new group.

    """
    gtool = getToolByName(context, 'portal_groups')
    gtool.addGroup(name, roles=roles, groups=groups)
    logger.info('Added group %s' % name)
    group = gtool.getGroupById(name)
    if members:
        for member in members:
            group.addMember(member)
            logger.info('Added member %s to group %s' % (member, name))


def add_user(context, username, password, email=None, fullname=None,
             roles=None, groups=None, data={}, logger=logger):
    """ Add a user to plone.

    @param context: A Plone context.

    @param username: The login name of the user.

    @param password: The password of the user.

    @param email: The Emailadress of the user.

    @param fullname: The fullname of the user.

    @param roles: A list of roles, the user should be in (e.g. "Manager").

    @param groups: A list of group, the user should be in.

    """
    pr = getToolByName(context, 'portal_registration')
    pm = getToolByName(context, 'portal_membership')
    acl_users = context.acl_users

    if acl_users.searchPrincipals(id=username, exact_match=True):
        logger.info('User %s exists already' % username)
        return

    pr.addMember(username, password)
    member = pm.getMemberById(username)
    member.setMemberProperties(dict(email=email, fullname=fullname))
#    member.setMemberProperties(dict(email=email,
#                               fullname=fullname).update(data)) #<-- TODO: binary data doesn't work. mabe this string doesn't even work. have to check.
    logger.info('Added user %s' % username)

    if roles is not None:
        acl_users.userFolderEditUser(username, password, roles, '')
        logger.info('Added roles %s to user %s' % (roles, username))

    if groups is not None:
        gtool = getToolByName(context, 'portal_groups')
        for group_id in groups:
            group = gtool.getGroupById(group_id)
            group.addMember(username)
            logger.info('Added user %s to group %s' % (username, group_id))


def create_item(ctx, id, item, logger=logger):
    """ Create an Archetype content item in the given context.
    This function is called by create_item_runner for each content found in
    it's given data structure.

    @param ctx: The context in which the item should be created.

    @param id: The identifier of the item to be created. If it exists, the
               item won't be created.

    @param item: A dictionary with the item configuration. See
                 create_item_runner for a more verbose explanation.

    @param logger: (Optional) A logging instance.

    """
    wft = getToolByName(ctx, 'portal_workflow')
    if not id in ctx.contentIds():
        ctx.invokeFactory(item['type'], id, title=item['title'], **item['data'])
        logger.info('created %s' % id)
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
    logger.info('configured %s' % id)


def create_item_runner(ctx, content, lang='en', logger=logger):
    """ Create Archetype contents from a list of dictionaries, where each
    dictionary describes a content item and optionally it's childs.

    @param ctx: The context in which the item should be created.

    @param content: The datastructure of the contents to be created. See
                    below.

    @param lang: The default language of the content items to be created.

    @param logger: (Optional) A logging instance.

    The datastructure of content is like so:

    [{'type': None,
      'id': None,
      'title': None,
      'data':{'description': None},
      'childs':[],
      'opts':{
          'lang': None,
          'setDefault': None,
          'setExcludeFromNav': None,
          'setLayout': None,
          'setLocallyAllowedTypes': None,
          'setImmediatelyAddableTypes': None,
          'workflow':None,}
    },]

    Use the same structure for each child. Leave out, what you don't need.

    """
    for item in content:
        if 'id' not in item:
            id = normalizeString(item['title'], context=ctx)
        else:
            id = item['id']
        if 'opts' not in item or not item['opts']: item['opts'] = {}
        if 'data' not in item or not item['data']: item['data'] = {}
        if 'lang' not in item['opts']: item['opts']['lang'] = lang
        create_item(ctx, id, item, logger=logger)
        if 'setDefault' in item['opts']: ctx.setDefaultPage(id)
        if 'childs' in item and item['childs']:
            create_item_runner(ctx[id], item['childs'], lang=lang,
                               logger=logger)


def delete_items(ctx, items, logger=logger):
    """ Remove content items from a context.

    @param ctx: Context, where items to be removed are in.

    @param items: List of item ids to be removed from context.

    @param logger: (Optional) A logging instance.

    """
    for id in items:
        if id in ctx.contentIds():
            ctx.manage_delObjects( [id] )
            logger.info('Removed %s' % id)


def hide_and_retract(item, hide=True, retract=True, logger=logger):
    """ Exclude an item from the navigation and retract it, if it was
    published. For example, to hide "Members" folder, if it shouldn't be
    shown to anonymous users.

    @param item: The item to hide and retract.

    @param logger: (Optional) A logging instance.

    """
    if hide:
        item.setExcludeFromNav(True)
        logger.info("%s excluded from navigation" % item.id)
    if retract:
        wft = getToolByName(item, 'portal_workflow')
        try:
            wft.doActionFor(item, 'retract')
            logger.info("%s unpublished (retracted)" % item.id)
        except:
            logger.warn("""Unpublishing (retracting) %s was not possible. Maybe
                        the item wasn't published or 'retract' transition not
                        available""" % item.id)


def isNotThisProfile(setup_context, marker_file):
    """ Return True if marker_file CANNOT be found in current profile's
    context. Used to exit a setuphandler step if it isn't called in
    profile's context.

    @param setup_context: The setuphandler context.

    @param marker_file: The name of the file which should be present in the
                        Profile's context.

    """
    return setup_context.readDataFile(marker_file) is None


def load_file(callers_globals, name, subdir=''):
    """ Load a file from a directory relative to the caller's module path and
    return it's data.

    @param callers_globals: The caller's globals dictionary. Can be retrieved
                            via globals(). Is used to get the caller's module
                            path.

    @param name: Name of the file to be loaded.

    @param subdir: subdirectory in current's package context.

    """
    module_path = os.path.dirname(
        sys.modules[callers_globals['__name__']].__file__
    )
    path = os.path.join(module_path, subdir, name)
    file_desc = open(path, 'rb')
    data = file_desc.read()
    file_desc.close()
    return data


def setup_portal_transforms(context, transform_id, transform_config,
                            logger=logger):
    """ Persistently configure a specific transformation in
    portal_transforms.

    @param context: A Plone context.

    @param transform_id: The transformation identifier (e.g. "safe_html")

    @param transform_config: A dictionary with the transformation
                             configuration.

    @param logger: (Optional) A logging instance.

    """
    pt = getToolByName(context, 'portal_transforms')
    if not transform_id in pt.objectIds(): return
    trans = pt[transform_id]

    tconfig = trans._config
    tconfig.update(transform_config)

    make_config_persistent(tconfig)
    trans._p_changed = True
    trans.reload()
    logger.info('portal_transform settings with id %s updated' % transform_id)


def unsafe_html_transform(context, logger=logger):
    """ Configure safe_html transformation from portal_transforms, so that
    it also allows embed and object elements.
    Also configure the style_whitelist to allow some styles needed for
    TinyMCE to bypass a limitation found in beta versions of Plone 4.0.

    @param context: A Plone context.

    @param logger: (Optional) A logging instance.

    """
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
                                  'color', 'width', 'height', 'padding-left',
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

    setup_portal_transforms(context, tid, tconfig, logger=logger)

def update_portlet_schema(context, portlet_interface, attribute, value,
        logger=logger):
    """
    Helper function to update a schema of an already registered portlet.

    @param context: A Plone context.

    @param portlet_interface: The interface that the portlet implements.

    @param attribute: The name of the attribute to be added as string.

    @param value: The value, the attribute should be initialized with.

    @param logger: (Optional) A logging instance.

    """
    from plone.portlets.interfaces import ILocalPortletAssignable
    from plone.portlets.interfaces import IPortletManager
    from plone.portlets.interfaces import IPortletAssignmentMapping
    from zope.component import getUtilitiesFor, getMultiAdapter

    urltool = getToolByName(context, "portal_url")
    site = urltool.getPortalObject()

    cat = getToolByName(site, 'portal_catalog')
    query = {'object_provides': ILocalPortletAssignable.__identifier__}
    all_brains = cat(**query)
    all_content = [brain.getObject() for brain in all_brains]
    all_content.append(site)
    for content in all_content:
        for manager_name, manager in getUtilitiesFor(IPortletManager, context=content):
            mapping = getMultiAdapter((content, manager), IPortletAssignmentMapping)
            for id, assignment in mapping.items():
                if portlet_interface.providedBy(assignment):
                    try:
                        getattr(assignment, attribute)
                        logger.info("attribute %s on portlet already set"
                            % attribute)

                    except AttributeError:
                        setattr(assignment, attribute, value)
                        logger.info("attribute %s on portlet set with value %s "
                            % (attribute, value))
