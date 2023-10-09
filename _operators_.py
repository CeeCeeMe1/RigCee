import bpy
from . import _functions_
import json
import math

class RIGCEE_OT_Save_Bone_Mapping(bpy.types.Operator):
    bl_idname = "armature.save_bone_mapping"
    bl_label = ""
    bl_description = "Save bone mapping"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bone_mapping = bpy.context.scene.bone_mapping_props.bone_mapping
        bone_mapping_file = bpy.path.abspath(bpy.context.scene.bone_mapping_props.bone_mapping_file)

        with open(bone_mapping_file, "w") as mappingfile:
            json.dump(bone_mapping, mappingfile, indent=4)

        self.report({'INFO'}, "Saved bone mapping successfully.")
        return {'FINISHED'}

class RIGCEE_OT_Load_Bone_Mapping(bpy.types.Operator):
    bl_idname = "armature.load_bone_mapping"
    bl_label = ""
    bl_description = "Load bone mapping"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bone_mapping_file = bpy.path.abspath(bpy.context.scene.bone_mapping_props.bone_mapping_file)

        with open(bone_mapping_file, 'r') as mappingfile:
            bone_mapping = json.load(mappingfile)

            for target_bone, import_bone in bone_mapping.items():
                bpy.context.scene.bone_mapping_props.bone_mapping[target_bone] = import_bone

        self.report({'INFO'}, "Loaded bone mapping successfully.")
        return {'FINISHED'}

class RIGCEE_OT_Rename_Bones(bpy.types.Operator):
    bl_idname = "armature.rename_bones"
    bl_label = "Rename and match skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import_armature = bpy.data.objects[bpy.context.scene.bone_mapping_props.import_armature]
        bone_mapping = bpy.context.scene.bone_mapping_props.bone_mapping

        inverse_bone_mapping = {v: k for k,v in bone_mapping.items()}
        bpy.context.view_layer.objects.active = import_armature

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        self.rename_bones(import_armature, inverse_bone_mapping) 
        bpy.ops.object.mode_set(mode='OBJECT')

        self.report({'INFO'}, "Renamed and merged weigths successfully.")
        return {'FINISHED'}

    def rename_bones(self, rig : bpy.types.Armature,
                    bone_mapping: dict[str,str]):
        bpy.context.view_layer.objects.active = rig

        meshes = _functions_.meshes_from_armature(rig)

        for import_name, other_name in bone_mapping.items():
            bpy.ops.object.mode_set(mode='EDIT')
            bone: bpy.types.EditBone = rig.data.edit_bones[import_name]
            bone.name = other_name

            bpy.ops.object.mode_set(mode='OBJECT')
            for mesh in meshes:
                if import_name in mesh.vertex_groups:
                    group: bpy.types.VertexGroup = mesh.vertex_groups[import_name]
                    group.name = other_name

        bpy.ops.object.editmode_toggle()

class RIGCEE_OT_Merge_To_Mapped_Parent(bpy.types.Operator):
    bl_idname = "armature.merge_to_mapped_parent"
    bl_label = "Rename and match skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import_armature = bpy.data.objects[bpy.context.scene.bone_mapping_props.import_armature]
        bone_mapping = bpy.context.scene.bone_mapping_props.bone_mapping

        weighted_bones = _functions_.get_weighted_bones_from_rig(import_armature)

        unmatched_weigthed_bones = list(set(weighted_bones) - set(bone_mapping.keys()))

        leaf_bones =  [bone for bone in unmatched_weigthed_bones
            if not import_armature.data.bones[bone].children]

        for bone in leaf_bones:
            self.merge_to_mapped_parent(import_armature, bone, set(bone_mapping.keys()))

        self.report({'INFO'}, "Renamed and merged weigths successfully.")
        return {'FINISHED'}

    def merge_to_mapped_parent(self,
                                rig : bpy.types.Armature,
                                bone_name : str,
                                mapped_bones: set[str]) -> list[str]:
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='EDIT')

        if bone_name in mapped_bones:
            return []

        bone: bpy.types.EditBone = rig.data.edit_bones[bone_name]

        if bone.parent:
            self.transfer_weights(rig, bone, bone.parent)
            self.merge_to_mapped_parent(rig, bone.parent.name, mapped_bones)


    def transfer_weights(self, rig, source: bpy.types.Bone, target: bpy.types.Bone):
        meshes = _functions_.meshes_from_armature(rig)

        for mesh in meshes:
            bpy.context.view_layer.objects.active = mesh

            weighted_bones = _functions_.get_weighted_bones(mesh)

            if (source.name in weighted_bones):
                bpy.ops.object.modifier_add(type='VERTEX_WEIGHT_MIX')

                bpy.context.object.modifiers.active.vertex_group_a = target.name
                bpy.context.object.modifiers.active.vertex_group_b = source.name
                bpy.context.object.modifiers.active.mix_mode = 'ADD'
                bpy.context.object.modifiers.active.mix_set = 'ALL'

                bpy.context.view_layer.objects.active = mesh

                bpy.ops.object.modifier_apply(modifier=bpy.context.object.modifiers.active.name)

        bpy.context.view_layer.objects.active = rig

class RIGCEE_OT_Match_Bone_Roll(bpy.types.Operator):
    bl_idname = "armature.match_bone_roll"
    bl_label = "Match bone roll"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import_armature_name = bpy.context.scene.bone_mapping_props.import_armature
        target_armature_name = bpy.context.scene.bone_mapping_props.target_armature

        if not import_armature_name or not target_armature_name:
            self.report({'ERROR'}, "Import and Target armature must be selected.")
            return {'CANCELLED'}

        import_armature = bpy.data.objects[import_armature_name]
        target_armature = bpy.data.objects[target_armature_name]

        self.match_bone_roll(target_armature, import_armature)

        bpy.ops.object.mode_set(mode='OBJECT')

        self.report({'INFO'}, "Transforms applied successfully.")
        return {'FINISHED'}

    def  match_bone_roll(self, from_rig : bpy.types.Armature, to_rig : bpy.types.Armature):
        print (f'matching bones from {from_rig.name} to {to_rig.name}')
        bpy.context.view_layer.objects.active = from_rig

        bpy.ops.object.mode_set(mode='EDIT')

        bone : bpy.types.EditBone

        rolls = {}

        for bone in from_rig.data.edit_bones:
            rolls[bone.name] = bone.roll

        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.context.view_layer.objects.active = to_rig

        bpy.ops.object.mode_set(mode='EDIT')

        bone : bpy
        for bone in to_rig.data.edit_bones:
            if bone.name in rolls:
                roll = rolls[bone.name]
                bone.roll = roll

        bpy.ops.object.mode_set(mode='OBJECT')

class RIGCEE_OT_Match_Pose(bpy.types.Operator):
    bl_idname = "armature.match_pose"
    bl_label = "Match pose"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import_armature_name = bpy.context.scene.bone_mapping_props.import_armature
        target_armature_name = bpy.context.scene.bone_mapping_props.target_armature
        start_bone_name = bpy.context.scene.bone_mapping_props.import_start_bone

        if not import_armature_name or not target_armature_name:
            self.report({'ERROR'}, "Import start bone, Import and Target armatures must be selected.")
            return {'CANCELLED'}


        import_armature = bpy.data.objects[import_armature_name]
        target_armature = bpy.data.objects[target_armature_name]

        self.match_bones(import_armature, target_armature, start_bone_name)

        bpy.ops.object.mode_set(mode='OBJECT')

        self.report({'INFO'}, "Transforms applied successfully.")
        return {'FINISHED'}

    def match_bones(self, other_rig : bpy.types.Armature, pose_rig : bpy.types.Armature, start_bone_name: str):
        print (f'matching bones from {pose_rig.name} to {other_rig.name}')

        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.context.view_layer.objects.active = pose_rig

        bpy.ops.object.mode_set(mode='POSE')
        # bpy.ops.armature.select_all(action='DESELECT')
        # for bone in bpy.context.view_layer.objects.active.pose.bones:
        #     for c in bone.constraints:
        #         bone.constraints.remove( c )

        bpy.context.object.pose.use_auto_ik = False
        bpy.context.object.pose.use_mirror_x = False

        bone: bpy.types.PoseBone = bpy.context.view_layer.objects.active.pose.bones[start_bone_name]

        self.match_recurse_children(other_rig, pose_rig, bone)


        bpy.ops.object.mode_set(mode='OBJECT')

        for mesh in _functions_.meshes_from_armature(pose_rig):
            print (f'updating mesh {mesh.name}')
            bpy.context.view_layer.objects.active = mesh

            armature_modifiers = [mod for mod in mesh.modifiers if mod.type == 'ARMATURE']

            armature_modifier = armature_modifiers[0]
            print (f'armature modifier count {len(armature_modifiers)}, using {armature_modifier.name}')

            bpy.ops.object.modifier_copy(modifier=armature_modifier.name)
            bpy.ops.object.modifier_apply(modifier=armature_modifier.name)

        bpy.context.view_layer.objects.active = pose_rig

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply(selected=False)
        bpy.ops.object.mode_set(mode='OBJECT')

    def match_recurse_children( self, 
                                other_rig : bpy.types.Armature,
                                pose_rig : bpy.types.Armature,
                                bone : bpy.types.PoseBone):

        if bone.name in other_rig.data.bones:
            other_bone: bpy.types.Bone = other_rig.data.bones[bone.name]

            self.copy_bone_information(bone, other_bone, other_rig)

            bpy.context.view_layer.update()
            bpy.ops.pose.visual_transform_apply()
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        for child_bone in bone.children:
            self.match_recurse_children(other_rig, pose_rig, child_bone)

    def copy_bone_information(self, bone: bpy.types.PoseBone, 
                               from_bone: bpy.types.Bone,
                               other_rig: bpy.types.Armature): 
        bone.bone.select = True

        added_constraints: list[bpy.types.Constraint] = []
        constraint_scale = bone.constraints.new('COPY_SCALE')
        constraint_scale.target = other_rig
        constraint_scale.subtarget = from_bone.name
        constraint_scale.target_space = 'WORLD'
        constraint_scale.owner_space = 'WORLD'

        added_constraints.append(constraint_scale)

        constraint_loc = bone.constraints.new('COPY_LOCATION')
        constraint_loc.target = other_rig
        constraint_loc.subtarget = from_bone.name

        added_constraints.append(constraint_loc)


        constraint_rot = bone.constraints.new('COPY_ROTATION')
        constraint_rot.target = other_rig
        # constraint.use_y = False
        # constraint_rot.euler_order = 'YXZ'
        constraint_rot.target_space = 'LOCAL'
        constraint_rot.owner_space = 'LOCAL'
        constraint_rot.subtarget = from_bone.name

        added_constraints.append(constraint_rot)

        # constraint_child = bone.constraints.new('LIMIT_ROTATION')
        # constraint_child.use_limit_x = False
        # constraint_child.use_limit_y = True
        # constraint_child.min_y = math.radians(-0.5)
        # constraint_child.max_y = math.radians(0.5)
        # constraint_child.use_limit_z = False

        # constraint_child.euler_order = 'YXZ'
        # constraint_child.owner_space = 'LOCAL'

        # added_constraints.append(constraint_child)

        bpy.ops.pose.visual_transform_apply()

        for constraint in added_constraints:
            bone.constraints.remove(constraint)

        bone.bone.select = False

class RIGCEE_OT_Swap_Rigs(bpy.types.Operator):
    bl_idname = "armature.swap_rigs"
    bl_label = "Swap rigs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import_armature_name = bpy.context.scene.bone_mapping_props.import_armature
        target_armature_name = bpy.context.scene.bone_mapping_props.target_armature

        if not import_armature_name or not target_armature_name:
            self.report({'ERROR'}, "Import and Target armatures must be selected.")
            return {'CANCELLED'}

        import_armature = bpy.data.objects[import_armature_name]
        target_armature = bpy.data.objects[target_armature_name]

        self.swap_rigs_and_weights(import_armature, target_armature)

        bpy.ops.object.mode_set(mode='OBJECT')

        self.report({'INFO'}, "Transforms applied successfully.")
        return {'FINISHED'}

    def swap_rigs_and_weights(self, source_rig: bpy.types.Armature,
                               other_rig: bpy.types.Armature):

        meshes = _functions_.meshes_from_armature(source_rig)

        for mesh in meshes:
            self.swap_rigs(mesh, source_rig, other_rig)

    def swap_rigs(self, mesh: bpy.types.Mesh, remove_rig: bpy.types.Armature, add_rig: bpy.types.Armature):
        print (f'swapping rig from {remove_rig.name} to {add_rig.name} for {mesh.name}')

        bpy.context.view_layer.objects.active = mesh
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = mesh
        _functions_.clearparent(mesh)

        bpy.ops.object.modifier_add(type='ARMATURE')
        bpy.context.object.modifiers["Armature"].object = add_rig
        bpy.ops.object.modifier_apply()


        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = remove_rig
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply(selected=False)

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = add_rig

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        add_rig.select_set(True)
        mesh.select_set(True)

        bpy.ops.object.parent_set(type='ARMATURE')

class RIGCEE_OT_Convert_Armature_For_Export(bpy.types.Operator):
    bl_idname = "armature.convert_armature_for_export"
    bl_label = "Remove helper rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature_name = bpy.context.scene.bone_mapping_props.target_armature
        start_bone_name = 'root' #bpy.context.scene.bone_mapping_props.import_start_bone

        if not armature_name:
            self.report({'ERROR'}, "Target armature must be selected.")
            return {'CANCELLED'}

        armature = bpy.data.objects[armature_name]

        bpy.context.view_layer.objects.active = armature

        bpy.ops.object.mode_set(mode='EDIT')

        rig_prefix = 'RIG_'
        _functions_.remove_constraints_recursive(armature.pose.bones[start_bone_name])
        self.add_prefix_recursive(armature.data.edit_bones[start_bone_name], rig_prefix)

        self.remove_prefix_recursive(armature.data.edit_bones['DEF_' + start_bone_name], 'DEF_')

        bpy.ops.object.mode_set(mode='POSE')
        _functions_.remove_constraints_recursive(armature.pose.bones[start_bone_name])

        self.transfer_vertex_groups2(armature, rig_prefix)
        self.set_bones_deform(armature)
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.context.view_layer.objects.active = armature

        bpy.ops.object.mode_set(mode='EDIT')
        self.remove_bones_recursive(armature.data.edit_bones[rig_prefix + start_bone_name])

        self.report({'INFO'}, "Transforms applied successfully.")
        return {'FINISHED'}

    def remove_bones_recursive(self, bone : bpy.types.EditBone):
        self.select_bones_recursive(bone, True)
        bpy.ops.armature.delete()

    def select_bones_recursive(self, bone: bpy.types.EditBone, select):
        bone.select = select

        for child in bone.children:
            self.select_bones_recursive(child, select)

    def remove_prefix_recursive(self, bone: bpy.types.EditBone, prefix):
        self.edit_prefix_recursive_exec(bone, prefix, False)

    def add_prefix_recursive(self, bone: bpy.types.EditBone, prefix):
        self.edit_prefix_recursive_exec(bone, prefix, True)

    def edit_prefix_recursive_exec(self, bone: bpy.types.EditBone, prefix, add):
        if (add):
            newname = prefix + bone.name
        else:
            newname = bone.name.removeprefix(prefix)

        bone.name = newname

        for child in bone.children:
            self.edit_prefix_recursive_exec(child, prefix, add)

    def get_bones_name_recursive(self, bone) -> list[str]:
        bones = []
        bones.append(bone.name)

        for child in bone.children:
            bones.extend(self.get_bones_name_recursive(child))

        return bones

    def transfer_vertex_groups2(self, import_armature: bpy.types.Armature, rig_prefix: str):
        bpy.ops.object.mode_set(mode='OBJECT')

        meshes = _functions_.meshes_from_armature(import_armature)

        mesh: bpy.types.Mesh

        for mesh in meshes:
            group: bpy.types.VertexGroup
            for group in mesh.vertex_groups:
                group.name = group.name.removeprefix(rig_prefix)

    def transfer_vertex_groups(self, import_armature: bpy.types.Armature, rig_prefix: str):
        meshes = _functions_.meshes_from_armature(import_armature)

        bpy.ops.object.mode_set(mode='OBJECT')

        bone_names = self.get_bones_name_recursive(import_armature.data.bones['pelvis'])

        for mesh in meshes:
            bpy.context.view_layer.objects.active = mesh

            for bone_name in bone_names:
                rig_bone_name = rig_prefix + bone_name

                bone : bpy.types.ArmatureBones
                bone = import_armature.data.bones[bone_name]
                bpy.ops.object.vertex_group_add()
                bpy.context.object.vertex_groups.active.name = bone_name
                bone.select = True
                bpy.ops.pose.group_assign()
                bone.use_deform = True
                bone.select = False

                bpy.ops.object.modifier_add(type='VERTEX_WEIGHT_MIX')
                vertex_weight_mix_modifier = bpy.context.object.modifiers.active
                vertex_weight_mix_modifier.vertex_group_a = bone_name
                vertex_weight_mix_modifier.vertex_group_b = rig_bone_name
                vertex_weight_mix_modifier.mix_mode = 'SET'
                vertex_weight_mix_modifier.mix_set = 'B'

                print (f'VERTEX_WEIGHT_MIX bone {bone_name} to {rig_bone_name} => {vertex_weight_mix_modifier.vertex_group_a} {vertex_weight_mix_modifier.vertex_group_b}')

                bpy.ops.object.modifier_apply()

        bpy.ops.object.mode_set(mode='OBJECT')

    def set_bones_deform(self, import_armature: bpy.types.Armature):
        bpy.ops.object.mode_set(mode='OBJECT')

        for bone in import_armature.data.bones:
            bone.use_deform = True