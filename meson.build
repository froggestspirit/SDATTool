project('SDATTool',
    meson_version: '>=1.2.0',
    version: '1.4.1'
)

subdir('SDATTool')

############################################################
###                    FOR CONSUMERS                     ###
############################################################

SDATTool_dep = declare_dependency()

meson.override_dependency('SDATTool', SDATTool_dep)
meson.override_find_program('SDATTool_py', SDATTool_py)
