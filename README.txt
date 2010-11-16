Introduction
============

Tools for Plone setuphandler steps when running Generic Setup import Steps.

SetupHandlerTools.create_item_runner: Create Archetype contents from a list of
dictionaries, where each dictionary describes a content item and optionally it's
childs.

SetupHandlerTools.isNotThisProfile: Return True if marker_file CANNOT be found
in current profile's context. Used to exit a setuphandler step if it isn't
called in profile's context.

SetupHandlerTools.add_calendar_type: Add calendar types to
Products.CMFPlone.CalendarTool.

SetupHandlerTools.load_file: Load a file from a directory and return it's data.

SetupHandlerTools.unsafe_html_transform: Configure safe_html transformation from
portal_transforms, so that it also allows embed and object elements. Also
configure the style_whitelist to allow some styles needed for TinyMCE to bypass
a limitation found in beta versions of Plone 4.0.

setup_portal_transforms: Persistently configure a specific transformation in
portal_transforms.


Author
======

Johannes Raggam <johannes at raggam dot co dot at>
BlueDynamics Alliance, 2010