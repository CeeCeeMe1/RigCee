import bpy
from . import _functions_
from typing_extensions import Self

def populate_armature_enum(self, context):
    armature_items = [(arm.name, arm.name, "") for arm in bpy.data.armatures]
    return armature_items

def populate_import_bones_enum(self, context):
    import_rig = bpy.data.objects[bpy.context.scene.bone_mapping_props.import_armature]
    bone_items = [(bone.name, bone.name, "") for bone in bpy.data.armatures[self.import_armature].bones]#_functions_.get_weighted_bones_from_rig(import_rig)]
    return bone_items

def populate_target_bones_enum(self, context):
    bone_items = [(bone.name, bone.name, "") for bone in bpy.data.armatures[self.target_armature].bones]
    return bone_items

def create_bone_mapping(self,context):
    target_armature = bpy.data.armatures[self.target_armature]
    import_armature = bpy.data.armatures[self.import_armature]
    import_rig_obj = bpy.data.objects[bpy.context.scene.bone_mapping_props.import_armature]

    weighted_bones = _functions_.get_weighted_bones_from_rig(import_armature)

    self.bone_mapping_enums.clear()
    self.bone_mapping.clear()

    import_bone = import_armature.bones[self.import_start_bone]
    candidates = _functions_.candidates(import_bone)
    weighted_candidates =[c for c in candidates if c.name in weighted_bones]
    weighted_candidates_names = [c.name for c in weighted_candidates]

    if import_bone.name in weighted_candidates_names:
        candidates = weighted_candidates

    create_bone_mapping_recurse(self, context,
                                import_armature,
                                target_armature.bones[self.target_start_bone],
                                import_bone,
                                candidates,
                                weighted_bones)

def get_import_bone_candidates(self, context):
    candidates = []
    for bone in self.import_bone_candidates:
        candidates.append((bone.bone, bone.bone, bone.bone))

    return candidates

def create_bone_mapping_recurse(self,context,
                                import_rig : bpy.types.Armature,
                                target_bone : bpy.types.Bone,
                                mapped_import_bone : bpy.types.Bone,
                                import_candidates : list[bpy.types.Bone],
                                weighted_bones: list[str]):
    mapping = [m for m in context.scene.bone_mapping_props.bone_mapping_enums if m.target_bone == target_bone.name]

    if mapping:
        bone_enum = mapping[0]
    else:
        bone_enum = context.scene.bone_mapping_props.bone_mapping_enums.add()
        bone_enum.name = target_bone.name
        bone_enum.target_bone = target_bone.name

    if not target_bone.name in bpy.context.scene.bone_mapping_props.bone_mapping:
        bpy.context.scene.bone_mapping_props.bone_mapping[target_bone.name] = mapped_import_bone.name

    bone_enum.import_bone_candidates.clear()

    # if not mapped_import_bone.name in import_candidates:
    #    import_candidates.append(mapped_import_bone)

    for bone in import_candidates:
        candidate = bone_enum.import_bone_candidates.add()
        candidate.name = bone.name
        candidate.bone = bone.name

    bone_enum.import_bone = mapped_import_bone.name

    child_candidates = _functions_.child_candidates(mapped_import_bone)
    weighted_child_candidates = [c for c in child_candidates if c.name in weighted_bones or not weighted_bones]
    weighted_child_candidates_names = [c.name for c in weighted_child_candidates]

    for target_child_bone in target_bone.children:
        mapped_import_child_bone = {}

        if weighted_child_candidates:
            if target_bone.name in bpy.context.scene.bone_mapping_props.bone_mapping:
                mapped_import_child_bone_name = bpy.context.scene.bone_mapping_props.bone_mapping[target_bone.name]

                # if mapped_import_child_bone_name in weighted_child_candidates_names:
                #     mapped_import_child_bone = import_rig.bones[mapped_import_child_bone_name]

            if not mapped_import_child_bone:
                mapped_import_child_bone = weighted_child_candidates[0]

            create_bone_mapping_recurse(self, context, import_rig, target_child_bone, mapped_import_child_bone, weighted_child_candidates, weighted_bones)

def update_bone_mapping(self,context):
    target_rig = bpy.data.armatures[bpy.context.scene.bone_mapping_props.target_armature]
    import_rig = bpy.data.armatures[bpy.context.scene.bone_mapping_props.import_armature]
    import_rig_obj = bpy.data.objects[bpy.context.scene.bone_mapping_props.import_armature]

    weighted_bones = _functions_.get_weighted_bones_from_rig(import_rig_obj)

    bpy.context.scene.bone_mapping_props.bone_mapping[self.target_bone] = self.import_bone

    mapped_import_bone = import_rig.bones[self.import_bone]
    candidates = _functions_.child_candidates(mapped_import_bone)
    weighted_candidates =[c for c in candidates if c.name in weighted_bones or not weighted_bones]

    if weighted_candidates:
        mapped_import_child_bone = weighted_candidates[0]

        for target_child in target_rig.bones[self.target_bone].children:
            create_bone_mapping_recurse(self, context, import_rig, target_child, mapped_import_child_bone, weighted_candidates, weighted_bones)

class RigCeeBoneProperty(bpy.types.PropertyGroup):
    bone: bpy.props.StringProperty(name="bone")

class RigCeeBonePairProperty(bpy.types.PropertyGroup):
    target_bone: bpy.props.StringProperty(name="target_bone")

    import_bone_candidates: bpy.props.CollectionProperty(type=RigCeeBoneProperty)

    import_bone: bpy.props.EnumProperty(name="import_bone",
        items=get_import_bone_candidates,
        update=update_bone_mapping,
        description="Import bone",
        default=None
    )

class RigCeeMappingPropertyGroup(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.bone_mapping_props = bpy.props.PointerProperty(type=RigCeeMappingPropertyGroup)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.bone_mapping_props

    import_armature: bpy.props.EnumProperty(
        items=populate_armature_enum,
        name="Import armature",
        description="Select an armature to rig",
        default=None
    )

    import_start_bone: bpy.props.EnumProperty(
        items=populate_import_bones_enum,
        update=create_bone_mapping,
        name="Import start bone",
        description="The central start point in the skeleton, ex: pelvis",
        default=None
    )

    target_armature: bpy.props.EnumProperty(
        items=populate_armature_enum,
        name="Target armature",
        description="Select the armature to rig to",
        default=None
    )

    target_start_bone: bpy.props.EnumProperty(
        items=populate_target_bones_enum,
        update=create_bone_mapping,
        name="Target start bone",
        description="The central start point in the skeleton, ex: pelvis",
        default=None
    )

    bone_mapping_file: bpy.props.StringProperty(name="Bone mapping file",
        description="Save or Load bone mapping from file",
        default="",
        subtype='FILE_PATH')

    bone_mapping: dict[str, str] = {}

    bone_mapping_enums: bpy.props.CollectionProperty(type=RigCeeBonePairProperty)
