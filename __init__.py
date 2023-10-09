# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "RigCee",
    "author" : "CeeCeeMe",
    "description" : "",
    "blender" : (3, 4, 0),
    "version" : (0, 1, 0),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

import bpy
from bpy.utils import (register_class, unregister_class)
from . import (_properties_, _operators_, _interface_)

RigCee_classes = [
    _properties_.RigCeeBoneProperty,
    _properties_.RigCeeBonePairProperty,
    _properties_.RigCeeMappingPropertyGroup,
    _operators_.RIGCEE_OT_Save_Bone_Mapping,
    _operators_.RIGCEE_OT_Load_Bone_Mapping,
    _operators_.RIGCEE_OT_Rename_Bones,
    _operators_.RIGCEE_OT_Merge_To_Mapped_Parent,
    _operators_.RIGCEE_OT_Match_Bone_Roll,
    _operators_.RIGCEE_OT_Match_Pose,
    _operators_.RIGCEE_OT_Swap_Rigs,
    _operators_.RIGCEE_OT_Convert_Armature_For_Export,
    _interface_.RIGCEE_MT_Presets,
    _interface_.RIGCEE_OT_Presets,
    _interface_.RIGCEE_PT_ArmatureSelectionPanel,
    _interface_.RIGCEE_PT_BoneMappingPanel,
    _interface_.RIGCEE_PT_BoneTreePanel,
    _interface_.RIGCEE_PT_ToolsPanel,
]

__register, __unregister = bpy.utils.register_classes_factory(RigCee_classes)

def register():
    __register()

def unregister():
    __unregister()
