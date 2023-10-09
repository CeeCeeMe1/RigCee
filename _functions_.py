import bpy

def meshes_from_armature2(armature: bpy.types.Armature) -> list[bpy.types.Mesh]:
    meshes = [child for child in armature.children
        if child.type == 'MESH'] #and child.find_armature()]

    return meshes

def meshes_from_armature(armature: bpy.types.Armature) -> list[bpy.types.Mesh]:
    meshes = []

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for modifier in obj.modifiers:
                if modifier.type == 'ARMATURE':
                    if modifier.object and modifier.object.name == armature.name:
                        meshes.append(obj)
    return meshes

def get_weighted_bones(mesh: bpy.types.Mesh) -> list[str]:
    bones = []
    for group in mesh.vertex_groups:
        bones.append(group.name)

    return bones

def get_weighted_bones_from_rig(rig: bpy.types.Armature):
    meshes = meshes_from_armature(rig)
    weighted_bones = []
    for mesh in meshes:
        weighted_bones.extend(get_weighted_bones(mesh))

    return weighted_bones

def siblings(bone: bpy.types.Bone) -> list[bpy.types.Bone]:
    if bone.parent:
        return candidates(bone.parent)
    else:
        return []

def child_candidates(bone: bpy.types.Bone, max_depth=3) -> list[bpy.types.Bone]:
    return _candidates_recurse(bone, max_depth, 0)

def candidates(bone: bpy.types.Bone, max_depth=3) -> list[bpy.types.Bone]:
    cand = []

    cand.append(bone)
    cand.extend(_candidates_recurse(bone, max_depth, 0))

    return cand

def _candidates_recurse(bone: bpy.types.Bone, max_depth=3, current_depth=0) -> list[bpy.types.Bone]:
    cand = []

    if current_depth < max_depth:
        for child in bone.children:
            cand.append(child)

        for child in bone.children:
            cand.extend(_candidates_recurse(child, max_depth, current_depth + 1))

    return cand

def clearparent(mesh: bpy.types.Mesh):
    bpy.context.view_layer.objects.active = mesh

    print ('remove parent for ' + mesh.name)
    bpy.ops.object.mode_set(mode='OBJECT')

    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh

    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    armature_mods = [mod for mod in mesh.modifiers if mod.type == 'ARMATURE']
    if armature_mods:
        mesh.modifiers.remove(armature_mods[-1])

    mesh.select_set(False)
    bpy.ops.object.select_all(action='DESELECT')

def remove_constraints_recursive(bone : bpy.types.PoseBone):
    for c in bone.constraints:
        bone.constraints.remove( c )

    for child in bone.children:
        remove_constraints_recursive(child)
