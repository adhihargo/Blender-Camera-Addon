'''
Copyright (C) 2014 Jacques Lucke
mail@jlucke.com

Created by Jacques Lucke

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

if "bpy" in locals():
    import importlib

    importlib.reload(su)
    importlib.reload(target_camera)
else:
    from . import sniper_utils as su
    from . import target_camera
import bpy


bl_info = {
    "name": "Sniper",
    "description": "Professional camera animations for motion graphics.",
    "author": "Jacques Lucke",
    "version": (1, 3, 2),
    "blender": (2, 80, 0),
    "location": "View 3D > Tool Shelf > Animation/Sniper",
    "category": "Animation"
}


# interface

class VIEW3D_PT_CameraTools(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animation"
    bl_label = "Sniper"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.operator("sniper.insert_target_camera", icon="OUTLINER_DATA_CAMERA")
        if target_camera.targetCameraSetupExists(): col.label(text="Settings are in 'Sniper' tab.", icon="INFO")

        col = layout.column(align=True)
        col.operator("sniper.separate_text")
        col.operator("sniper.text_to_name")


# operators

class SNIPER_OT_TextToName(bpy.types.Operator):
    bl_idname = "sniper.text_to_name"
    bl_label = "Text to Name"
    bl_description = "Rename all text objects to their content."

    def execute(self, context):
        su.textToName()
        return {"FINISHED"}


class SNIPER_OT_SeparateText(bpy.types.Operator):
    bl_idname = "sniper.separate_text"
    bl_label = "Seperate Text"
    bl_description = "Create new text object for every line in active text object."

    def execute(self, context):
        active = su.getActive()
        if su.isTextObject(active):
            su.separateTextObject(active)
            su.delete(active)

        return {"FINISHED"}


# registration

classes = (
    VIEW3D_PT_CameraTools,
    SNIPER_OT_TextToName,
    SNIPER_OT_SeparateText,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    target_camera.register()


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    target_camera.unregister()


if __name__ == "__main__":
    register()
