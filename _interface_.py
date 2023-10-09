import bpy
from bl_operators.presets import AddPresetBase
import os
from . import _functions_

class RIGCEE_MT_Presets(bpy.types.Menu):
    bl_label = "RigCee presets"
    bl_description = "Save settings (bone mapping filename is saved but not the mapping itself)"
    preset_subdir = "RigCee"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset

class RIGCEE_OT_Presets(AddPresetBase, bpy.types.Operator):
    bl_idname = "rigcee.preset_add"
    bl_label = "Bone Mapping Presets"
    preset_menu = "RIGCEE_MT_Presets"

    @classmethod
    def register(cls):
        my_presets = os.path.join("presets", "RigCee")
        # if not os.path.isdir(my_presets): 
        #     os.makedirs(my_presets)

    preset_defines = [
        "scene = bpy.context.scene"
    ]

    preset_values = [
        "scene.bone_mapping_props.target_armature",
        "scene.bone_mapping_props.import_armature",
        "scene.bone_mapping_props.target_start_bone",
        "scene.bone_mapping_props.import_start_bone",
        "scene.bone_mapping_props.bone_mapping_file"
    ]

    preset_subdir = RIGCEE_MT_Presets.preset_subdir

class RIGCEE_PT_ArmatureSelectionPanel(bpy.types.Panel):
    bl_label = "Armature selection"
    bl_idname = "RIGCEE_PT_ArmatureSelectionPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RigCee"

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.menu("RIGCEE_MT_Presets", text=RIGCEE_MT_Presets.bl_label, icon='PRESET')
        row.operator("rigcee.preset_add", text="", icon='ADD')
        row.operator("rigcee.preset_add", text="", icon='REMOVE').remove_active = True

        mapping_props = context.scene.bone_mapping_props

        layout.prop(mapping_props, "import_armature", icon='ARMATURE_DATA')
        layout.prop(mapping_props, "target_armature", icon='ARMATURE_DATA')

class RIGCEE_PT_BoneMappingPanel(bpy.types.Panel):
    bl_label = "Bone mapping"
    bl_idname = "RIGCEE_PT_BoneMappingPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RigCee"

    def draw(self, context):
        layout = self.layout

        mapping_props = context.scene.bone_mapping_props

        layout.prop(mapping_props, "import_start_bone", icon='BONE_DATA')
        layout.prop(mapping_props, "target_start_bone", icon='BONE_DATA')

        row = layout.row(align=True)
        row.prop(mapping_props, "bone_mapping_file")
        row.operator("armature.save_bone_mapping", icon='EXPORT')
        row.operator("armature.load_bone_mapping", icon='IMPORT')

        row = layout.row()
        row.operator('armature.rename_bones', text="Rename bones")

class RIGCEE_PT_BoneTreePanel(bpy.types.Panel):
    bl_label = "Bone tree"
    bl_idname = "RIGCEE_PT_BoneTreePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RigCee"

    def draw(self, context):
        layout = self.layout

        mapping_props = context.scene.bone_mapping_props
        target_armature = bpy.data.armatures[mapping_props.target_armature]

        weighted_bones = _functions_.get_weighted_bones_from_rig(target_armature)

        self.draw_bone_tree(layout, mapping_props, target_armature.bones[mapping_props.target_start_bone])

    def draw_bone_tree(self, layout, mapping_props, startbone):

        for bone in startbone.children:
            row = layout.row(align=True)
            col = row.column()
            col.label(text=bone.name)

            if bone.name in mapping_props.bone_mapping.keys() and bone.name in mapping_props.bone_mapping_enums:
                col.prop(mapping_props.bone_mapping_enums[bone.name], "import_bone", text="")

            col = row.column()
            self.draw_bone_tree(col, mapping_props, bone)

class RIGCEE_PT_ToolsPanel(bpy.types.Panel):
    bl_label = "Tools"
    bl_idname = "RIGCEE_PT_ToolsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RigCee"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator('armature.merge_to_mapped_parent', text="Merge unmapped to parent")
        row = layout.row()
        row.operator('armature.match_bone_roll', text="Match bone roll")
        row = layout.row()
        row.operator('armature.match_pose', text="Match pose")
        row = layout.row()
        row.operator('armature.swap_rigs', text="Swap Rigs")
        row = layout.row()
        row.operator('armature.convert_armature_for_export', text="Remove helper rig")
        row = layout.row()
        # Skeleton'/Game/Core/Assets/Skeletons/ALS_Mannequin_Skeleton.ALS_Mannequin_Skeleton'
