import bpy
import mathutils


# ------------------- get_pole_angle --------------#
# This function calculates the pole angle for the IK constraint
# It takes three bones as input: base, middle, and pole
# The base and middle bones are used to calculate the pole normal
# The pole bone is used to calculate the pole angle
# The function returns the pole angle in radians
# The pole angle is the angle between the base bone's x-axis and the projected pole axis on the base bone's plane
def get_pole_angle(base, middle, pole):
    def get_signed_angle(vector_u, vector_v, normal):

        uv_angle = vector_u.angle(vector_v)

        if vector_u.cross(vector_v) == mathutils.Vector((0, 0, 0)):
            return uv_angle

        if vector_u.cross(vector_v).angle(normal) < 1:
            return -uv_angle

        return uv_angle

    pole_location = pole.head

    pole_normal = (middle.tail - base.head).cross(pole_location - base.head)
    projected_pole_axis = pole_normal.cross(base.vector)

    pole_angle = get_signed_angle(base.x_axis, projected_pole_axis, base.vector)

    return pole_angle


# ------------------- generate rig --------------#
# Generate rig bones position
# This operator generates the rig bones position based on the selected object and armature
class GenerateRig(bpy.types.Operator):
    bl_idname = "fg.generate_rig"
    bl_label = "Orient rig bones position"
    bl_description = "Generate rig bones position"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        if not hasattr(context.scene, "my_object") or context.scene.my_object is None:
            self.report({"ERROR"}, "No object set in the scene")
            return {"CANCELLED"}
        if not hasattr(context.scene, "my_armature") or not context.scene.my_armature:
            self.report({"ERROR"}, "No armature set in the scene")
            return {"CANCELLED"}

        human = context.scene.my_object
        armatur = context.scene.my_armature
        armatur.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.context.view_layer.objects.active = armatur
        bpy.context.object.data.pose_position = "REST"
        editbones = armatur.data.edit_bones
        bonenames = [bn.name for bn in editbones]

        human.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        tall = human.dimensions[2] / 57
        width = human.dimensions[0] / 2
        deep = human.dimensions[1]

        center = tall * 30.5
        armlocz = tall * 47
        armlocx = 0
        # 3. Axis vectors
        x_axis = mathutils.Vector((1, 0, 0))
        y_axis = mathutils.Vector((0, 1, 0))
        z_axis = mathutils.Vector((0, 0, 1))

        matrixworld = human.matrix_world
        allverts = [matrixworld @ v.co for v in human.data.vertices]
        allverts2 = [v for v in human.data.vertices if v.co.x > 0]

        verts = [v for v in allverts if abs(v.x) < 0.1]
        uppest = max(verts, key=lambda v: v.z)
        # print("uppest: ", uppest)  # uppest:  <Vector (0.0006, -0.0340, 1.6413)>
        bones = ["spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006"]
        lengths = [2.5, 3, 6.5, 4.5, 2.5, 1.5, 6]
        ypos = [0.5, 0, -0.3, 0, 1.2, 0.5, 0.08]

        # arms =["shoulder.L","upper_arm.L","forearm.L","hand.L"]
        # armlen=[6,10,8,3]
        bpy.ops.object.mode_set(mode="EDIT")
        i = 0
        for bn in bones:

            if not bn in bonenames:
                editbones.new(bn)
            editbones[bn].head.x = 0
            editbones[bn].tail.x = 0
            # editbones[bn].head.y = 0

            editbones[bn].roll = 0
            editbones[bn].use_deform = True
            if i != 0:
                editbones[bn].use_connect = True
                editbones[bones[i]].parent = editbones[bones[i - 1]]

            editbones[bn].head.z = center
            center += lengths[i] * tall
            editbones[bn].tail.z = center
            editbones[bn].color.palette = "THEME04"

            verty = [v for v in verts if abs(editbones[bn].head.z - v.z) < tall / 2 and abs(editbones[bn].head.x - v.x) < tall / 2]
            maxy = max(verty, key=lambda v: v.y).y
            miny = min(verty, key=lambda v: v.y).y
            if not maxy and not miny:
                editbones[bn].head.y = ypos[i] * tall + uppest.y
                editbones[bn].tail.y = ypos[i] * tall + uppest.y
            else:
                editbones[bn].head.y = maxy * 0.55 + miny * 0.45
                editbones[bn].tail.y = maxy * 0.55 + miny * 0.45
                # print("maxy: ", maxy, "miny: ", miny)

            editbones[bn].envelope_distance = editbones[bn].length / 4
            # print(editbones[bn], editbones[bn].length)
            i += 1

        #********************************************************#
        # ----------------------------------arms------------------#
        # allverts2 = [v for v in human.data.vertices if v.co.x > 0]
        arms = ["shoulder.L", "upper_arm.L", "forearm.L", "hand.L"]
        armsh = []
        for arm in arms:
            armsh.append(editbones[arm])
            editbones[arm].color.palette = "THEME05"
            editbones[arm].envelope_distance = editbones[arm].length / 4

        # --------------arm pit ------shoulder------
       

        allv = [v for v in allverts2 if v.co.x> tall*3.5]
        zz = max(allv, key=lambda v: v.co.z )
        zzz=zz.co.copy()
        zzz.x += tall
        zzz.z -= tall*2
        
        armsh[1].head = zzz
        armsh[0].tail = armsh[1].head
        armsh[0].head = armsh[1].head + mathutils.Vector((-tall * 4, 0, 0))
        armsh[0].tail.z += tall

        # -----hand---------------

        handvert = [v.co for v in allverts2 if abs(v.co.x - width) < tall]
        handy = max(handvert, key=lambda v: v.x)
        handz = max(handvert, key=lambda v: v.z)
        armz=zzz-handz
        # handy.y = handy.y - tall * 2
        editbones["hand.L"].tail = handy

        # --------------------elbow-------------

        midelbow = editbones["upper_arm.L"].head * 0.5 + editbones["hand.L"].tail * 0.5
        # print("mid1elbow: ", midelbow)
        elbowvert = [v.co for v in allverts2 if abs(v.co.x - midelbow.x) < tall and abs(v.co.z - midelbow.z) < tall]
        # for v in allverts2:
        #     if abs(v.co.x - midelbow.x) < tall and abs(v.co.z - midelbow.z) < tall:
        #         v.select = True
        elbowymx = max(elbowvert, key=lambda v: v.y)
        elbowymn = min(elbowvert, key=lambda v: v.y)
        elbowy = elbowymx * 0.5 + elbowymn * 0.5
        editbones["upper_arm.L"].tail = elbowy

        wristvert = [v for v in allverts if abs(v.x - (width * 0.9)) < tall]
        wristy = max(wristvert, key=lambda v: v.y)
        wristy.y = wristy.y - tall
        editbones["forearm.L"].tail = wristy

        # -------------------legs-------------------------------#
        legs = ["thigh.L", "shin.L", "foot.L", "toe.L"]
        legsh = []
        for leg in legs:
            legsh.append(editbones[leg])
            editbones[leg].color.palette = "THEME11"
            editbones[leg].envelope_distance = editbones[leg].length / 4
        # ------------------------thigh------
        legsh[0].head = editbones["spine"].head
        legsh[0].head.x = 2.5 * tall
        #---------shin----------knee----------------
        kneevert = [v for v in allverts if abs(v.z - tall * 15) < tall and v.x > 0]
        kneey = min(kneevert, key=lambda v: v.y)
        kneey.y = kneey.y + tall
        legsh[0].tail = kneey
        #----------------ankle-foot----------------
        anklevert = [v for v in allverts if abs(v.z - tall * 4) < tall and v.x > 0]
        anklez = min(anklevert, key=lambda v: v.y)
        anklez.y = anklez.y + tall * 1.5
        legsh[1].tail = anklez
        #-----------------foot---toe-------------
        toevert = [v for v in allverts if abs(v.z - tall) < tall and v.x > 0]
        toey = min(toevert, key=lambda v: v.y)
        toey.y = toey.y + tall * 2
        legsh[2].tail = toey
        legsh[3].tail = toey - mathutils.Vector((0, 2 * tall, 0))

        # for bn in arms:
        #     if not bn in orjbn:
        #         editbones.new(bn)
        #     if j>0:
        #         editbones[bn].parent = editbones[arms[j-1]]
        #     editbones[bn].head.z = armlocz
        #     editbones[bn].tail.z = armlocz

        #     editbones[bn].head.x=armlocx
        #     armlocx += armlen[j]*tall
        #     editbones[bn].tail.x = armlocx

        #     editbones[bn].use_connect =True

        #     j += 1
        bpy.context.object.data.pose_position = "POSE"
        bpy.ops.object.mode_set(mode=mode)
        self.report({"INFO"}, f"Rig created for armature: {armatur.name}")
        return {"FINISHED"}


# ------------------- generate ik --------------#
# Generate ik bones for arm or leg
class GenerateIk(bpy.types.Operator):
    bl_idname = "fg.generate_ik"
    bl_label = "Genx ik"
    bl_description = "Generate ik bones for arm or leg"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.context.object.pose.use_mirror_x = False
        bpy.context.object.data.pose_position = "REST"

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.context.object.data.use_mirror_x = False
        edit_bones = context.object.data.edit_bones
        activebone = context.active_bone  # context.object.data.edit_bones.active
        ac = edit_bones.get(activebone.name)

        base = activebone.parent
        dir = (ac.vector - base.vector).normalized()
        # dir.z = 0
        # dir.x = 0
        if not base:
            self.report({"ERROR"}, "No parent bone to ik bone")
            return {"CANCELLED"}
        if not ac:
            self.report({"ERROR"}, "No ik bone selected")
            return {"CANCELLED"}

        # generate ik bone and place it
        activebonename = activebone.name
        bones = [bn.name for bn in edit_bones]
        ikbonename = "ik_" + activebone.name
        polebonename = "pole_" + activebone.name
        if not ikbonename in bones:
            ikbone = edit_bones.new(name=ikbonename)
        else:
            ikbone = edit_bones[ikbonename]
        if not polebonename in bones:
            polebone = edit_bones.new(name=polebonename)
        else:
            polebone = edit_bones[polebonename]

        ikbone.use_deform = False
        ikbone.head = activebone.tail
        if activebone.tail[2] > 0.66:
            t = 1
        else:
            t = -1
        ikbone.tail = ikbone.head + t * dir * 0.1

        # generate pole bone and place it
        polebone.use_deform = False
        polebone.head = base.tail + dir * ac.length * -3
        polebone.tail = polebone.head + dir * 0.1
        pol_angle = get_pole_angle(edit_bones[activebonename].parent, edit_bones[activebonename], edit_bones[polebonename])

        bpy.ops.object.mode_set(mode="POSE")
        activepbone = context.object.pose.bones[activebonename]
        if not "ik_" + activebonename in activepbone.constraints:
            cons = activepbone.constraints.new(type="IK")
            cons.name = "ik_" + activebonename
        else:
            cons = activepbone.constraints["ik_" + activebonename]

        cons.target = context.object
        cons.subtarget = ikbonename
        cons.pole_target = context.object
        cons.pole_subtarget = polebonename
        cons.pole_angle = pol_angle
        # print("uv_angle: ", cons.pole_angle)
        cons.chain_count = context.scene.chain_count
        cons.use_stretch = False

        bpy.context.object.data.pose_position = "POSE"

        # bpy.context.view_layer.update()
        self.report({"INFO"}, f"Ik bone created: {ikbonename}")
        return {"FINISHED"}


# ------------------- autoparent --------------#
# Auto parent the selected object to the armature
class Autoparent(bpy.types.Operator):
    bl_idname = "fg.autoparent"
    bl_label = "parent them"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mode = bpy.context.object.mode
        aktiv = bpy.context.active_object
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        human = context.scene.my_object
        armatur = context.scene.my_armature

        human.select_set(True)
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        armatur.select_set(True)
        bpy.context.view_layer.objects.active = armatur
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.context.object.data.pose_position = "REST"

        original_scale = armatur.scale.copy()
        human_scale = human.scale.copy()
        # --- Apply temporary scale (2x) ---
        armatur.scale = [s * 10 for s in original_scale]
        human.scale = [s * 10 for s in human_scale]
        # bpy.context.view_layer.update()

        bpy.ops.object.parent_set(type="ARMATURE_AUTO")

        armatur.scale = original_scale

        # bpy.context.view_layer.update()
        bpy.context.object.data.pose_position = "POSE"
        bpy.context.view_layer.objects.active = human
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = aktiv
        bpy.ops.object.mode_set(mode=mode)
        self.report({"INFO"}, f"Lets parent anyway")
        return {"FINISHED"}


# ------------------- weight paint auto --------------#
# Calculate the distance from a point to a line segment defined by two endpoints
def point_line_distance(point, line_start, line_end):
    """Calculate the distance from a point to a line segment defined by two endpoints."""
    line_vector = line_end - line_start
    point_vector = point - line_start
    line_length_squared = line_vector.length_squared

    if line_length_squared == 0:
        return (point - line_start).length

    t = max(0, min(1, point_vector.dot(line_vector) / line_length_squared))
    projection = line_start + t * line_vector
    return (point - projection).length


class Weightpaintauto(bpy.types.Operator):
    bl_idname = "fg.wpaintauto"
    bl_label = "auto weight paint"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        human = context.scene.my_object
        armatur = context.scene.my_armature
        # human.select_set(True)
        armatur.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.context.view_layer.objects.active = armatur
        verts = [v for v in human.data.vertices]
        # for v in verts:
        #     v.select=False
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.context.object.data.pose_position = "REST"

        bns = context.selected_editable_bones
        for bn in bns:
            for v in verts:
                world_co = human.matrix_world @ v.co
                headco = armatur.matrix_world @ bn.head
                tailco = armatur.matrix_world @ bn.tail
                if abs(point_line_distance(world_co, headco, tailco)) <= 0.01:
                    v.select = True
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = human
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}

    ############################################


# ------------------ register -------------------#
classes = [GenerateIk, GenerateRig, Weightpaintauto, Autoparent]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
