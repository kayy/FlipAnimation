#!BPY
# ***** BEGIN GPL LICENSE BLOCK *****
#
# Script copyright (C) Kay Bothfeld
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
# Revision $Id: FlipAnimation.py 929 2013-03-25 08:37:50Z kay $

import bpy

bl_info = {
    "name": "Flip Animation",
    "description": "Performs a copy and paste flipped pose on all frames of currently selected action.",
    "author": "Kay Bothfeld",
    "version": (0,3),
    "blender": (2,5,8),
    "location": "View3D > Pose Mode > Tool Shelf",
    "warning": "", # used for warning icon and text in addons panel 
    "wiki_url": "http://www.scio.de/en/blog-a-news/scio-development-blog-en/entry/flip-animation-add-on-for-mirroring-keyframes-in-blender",
    "link": "http://www.scio.de/en/blog-a-news/scio-development-blog-en/entry/flip-animation-add-on-for-mirroring-keyframes-in-blender",
    "tracker_url": "http://www.scio.de/",
    "category": "Animation"
    }

class FlipAnimationPanel(bpy.types.Panel) :
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "posemode"
    bl_label = "Flip Animation"
 
    def draw(self, context) :
        col = self.layout.column(align = True)
        col.prop(context.scene, "flip_animation_append_mode")
        if context.scene.flip_animation_append_mode:
            col.prop(context.scene, "flip_animation_start_frame")
            col.prop(context.scene, "flip_animation_end_frame")
            col.label("")
        col.operator("pose.flip_animation", text = "Flip Animation")


class FlipAnimation (bpy.types.Operator) :

    # Set this True to get noisy console output (MacOS/Linux users have to start Blender from terminal)
    debug_output = False
    # If True, code is executed for one frame only specified by initial_frame
    append_mode = False 
    
    # dict of dict: Outer dict contains (frame num, dict), inner (bone, deletion flag)
    keyframe_bone_dict = None
    # statistics
    num_changed = 0
    num_deleted = 0
    # Frame that was selected at the start of this plugin
    initial_frame = 0
    # Bone selection  at the start of this plugin, used to restore at the end
    initial_bone_selection = list()
    # Active bone  at the start of this plugin, used to restore at the end
    initial_active_bone = None
    # Range used for flipping poses, either the whole action or specified by user when append_mode = True
    start_frame = 0
    end_frame = 0
    # if append_mode = True this contains the offset where to paste the X flipped keyframes
    append_frames_offset = 0
    active_action = None
    
    bl_idname = "pose.flip_animation"
    bl_label = "Flip Animation"
    bl_options = {"REGISTER", "UNDO"}
    # bl_idname = "OBJECT_PT_ShowButtons"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "posemode"
    text = "Flip whole animation"

    def draw(self, context) :
        col = self.layout.column(align = True)
        
    def execute(self, context) :
        self.action_common(context)
        return {"FINISHED"}
 
    def invoke(self, context, event) :
        self.action_common(context)
        return {"FINISHED"}

    def action_common(self, context) :
        if self.check_preconditions (context):
            if self.debug_output :
                print("-------------------------------------- ", self.active_action.name, " (", self.start_frame, " - ", self.end_frame, 
                    "keying set: ", context.scene.keying_sets.active.name, ") ----------------------------------------")
            self.keyframe_bone_dict = self.build_keyframe_bone_dict (context, self.start_frame, self.end_frame)
            if self.append_mode:
                self.delete_keyframes_for_frame_mode (context)
            else:
                self.mark_keyframes_for_deletion (context)
            if self.debug_output :
                self.debug_print_keyframe_bone_dict ()
                print ("------------- \n")
            self.invert_all_key_frames (context)
            if not self.append_mode:
                self.delete_unneeded_key_frames (context, self.keyframe_bone_dict)
            self.report({'INFO'}, "Flipped action %s [%d; %d]: %d modified, %d deleted" % (self.active_action.name, self.start_frame, self.end_frame, self.num_changed, self.num_deleted))
            # restore initial status
            context.scene.frame_set(self.initial_frame)
            bpy.context.active_object.data.bones.active=self.initial_active_bone
            bpy.ops.pose.select_all(action='DESELECT')
            for bone in self.initial_bone_selection:
                if self.debug_output :
                    print("selecting ", bone)
                bpy.context.active_object.data.bones[bone].select = True
                    
    def check_preconditions (self, context):
        ok = True
        messages = list()
        self.num_changed = 0
        self.num_deleted = 0
        self.append_frames_offset = 0
        self.initial_frame = context.scene.frame_current
        self.append_mode = context.scene.flip_animation_append_mode
        if len(bpy.data.armatures) < 1: 
            # Should never occur because of pose mode but who knows
            self.report({'WARNING'}, "No armature found!")
            return False
        if context.active_object.animation_data == None:
            self.report({'WARNING'}, "Object has no animation data!")
            return False
        self.active_action = context.active_object.animation_data.action
        if self.active_action == None:
            self.report({'WARNING'}, "Please select an action to run 'Flip Animation' on!")
            return False
        action_first_frame = self.active_action.frame_range[0]
        action_last_frame = self.active_action.frame_range[1]
        if self.append_mode:
            ctx_start = context.scene.flip_animation_start_frame
            ctx_end = context.scene.flip_animation_end_frame
            if ctx_start > ctx_end:
                self.report({'WARNING'}, "'Start frame' (%d) is greater then 'End frame' (%d)!" % (ctx_start, ctx_end))
                return False
            self.start_frame = min(action_last_frame, max(ctx_start, action_first_frame))
            if self.start_frame != ctx_start:
                self.report({'WARNING'}, "'Start frame' (%d) is is outside the action's frame range' %d-%d!" % (ctx_start, action_first_frame, action_last_frame))
                return False
            self.end_frame = max(action_first_frame, min(ctx_end, action_last_frame))
            if self.end_frame != ctx_end:
                self.report({'WARNING'}, "'End frame' (%d) is is outside the action's frame range' %d-%d!" % (ctx_end, action_first_frame, action_last_frame))
                return False
            self.append_frames_offset = self.end_frame - self.start_frame
        else:   
            self.start_frame = action_first_frame
            self.end_frame = action_last_frame
        if self.start_frame > self.end_frame:
            self.report({'WARNING'}, "'Start frame' (%d) is greater then 'End frame' (%d)!" % (self.start_frame, self.end_frame))
            return False
        automatic_keyframe_insertion_ok=True
        if not context.tool_settings.use_keyframe_insert_auto:
            messages.append ("'Automatic Keyframe Insertion for Objects And Bones' button")
            automatic_keyframe_insertion_ok = False
        if not context.tool_settings.use_keyframe_insert_keyingset:
            messages.append ("'Automatic Keyframe Insertion Using Active Keying Set Only' button")
            automatic_keyframe_insertion_ok = False
        if not automatic_keyframe_insertion_ok:
            s = ""
            i = 0
            for message in messages: # if both buttons are not set, display 2 warnings at once to not annoy the user
                i += 1
                if i > 1:
                    s += " and "
                s +=  "(" + str(i) + ")" + message
            s = str(i) + " warnings: " + s + (" has" if i == 1 else " have")  + " to be set in Timeline View!"
            self.report({'WARNING'}, s)
            return False;
        self.initial_active_bone = context.active_bone
        self.initial_bone_selection = list()    
        for bone in bpy.context.active_object.data.bones:
            if bone.select:
                self.initial_bone_selection.append(bone.name)
        return True
            
    # Build a dictionary for iteration: Outer dict contains (frame num, dict), inner (bone, deletion flag)
    def build_keyframe_bone_dict (self, context, dict_start_frame, dict_end_frame, default_value='keep'):
        new_keyframe_bone_dict = dict()
        # iterate through all bones that have keyframes set in this action
        for g in self.active_action.groups:
            bone = g.name
            # iterate through all f-curves of the current bone
            for fcurve in g.channels:
                # iterate through all keyframes of the current f-curve
                for keyframe in fcurve.keyframe_points:
                    i = keyframe.co[0] # the current frame
                    if i >= dict_start_frame and i <= dict_end_frame:
                        if i in new_keyframe_bone_dict:
                            # this frame has a list from other bones already, add this bone 
                            key_seq = new_keyframe_bone_dict[i]
                        else:
                            # this frame has not yet been registered a bone dict
                            key_seq = dict()
                        # temporaryly we assume this bone to be kept, might be changed to 
                        # "deleted" in next step when mark_keyframes_for_deletion detects that it's disturbing 
                        key_seq[bone] = default_value
                        new_keyframe_bone_dict[i] = key_seq
        return new_keyframe_bone_dict
        
    
    def delete_keyframes_for_frame_mode (self, context):
        delete_keyframe_bone_dict = self.build_keyframe_bone_dict (context, self.end_frame + 1,
            self.end_frame + self.append_frames_offset, default_value='delete')
        self.delete_unneeded_key_frames(context, delete_keyframe_bone_dict)
    
    # In whole action mode (append_mode = False), iterate through all bones and set deletion mark for post-processing
    def mark_keyframes_for_deletion (self, context):
        for frame in self.keyframe_bone_dict.items ():
            for bone_item in frame[1].items ():
                bone = bone_item[0]
                bpy.ops.pose.select_all(action='DESELECT')
                prev_active_bone = context.active_bone.name
                bpy.context.active_object.data.bones.active=bpy.context.active_object.data.bones[bone]
                result = None
                result = bpy.ops.pose.select_flip_active()
                next_active_bone = context.active_bone.name
                if 'FINISHED' in result:
                    if self.debug_output:
                        print("Found flipped for active bone '", bone, "' -> ", next_active_bone) 
                    other_bone = next_active_bone
                    if bone == other_bone:
                        print ("ERROR! Bone ", bone, " could be flipped successfully but result is the bone itself: ", other_bone)
                        other_bone = "ERROR_ASDF_QWER_FDSA_REWQ"
                elif 'CANCELLED' in result: # 'CANCELLED' means there is no corresponding bone
                    if self.debug_output:
                        print("No flipped bone for '", bone, "'")
                    other_bone = ""
                else:
                    print("Error! Result bpy.ops.pose.select_flip_active() does neither contain 'FINISHED' nor 'CANCELLED'! Got:", result)
                    other_bone = ""
                if other_bone in frame[1] or other_bone == "":
                    # print ("Got ", bone, " other_bone is ", other_bone, " frame[1]", frame[1])
                    value = "keep"
                else:
                    value = "delete"
                key_seq = self.keyframe_bone_dict[frame[0]]
                key_seq[bone] = value
        
            
    # Apply copy and X-flipped paste operators to all keyframes defined in member var keyframe_bone_dict
    def invert_all_key_frames (self, context):
        for frame_item in self.keyframe_bone_dict.items ():
            frame = frame_item[0]
            if self.append_mode and frame == self.start_frame:
                continue
            out = ""
            bones = frame_item[1]
            context.scene.frame_set(frame)
            bpy.ops.pose.select_all(action='DESELECT')
            for bone_item in bones.items ():
                self.num_changed += 1
                bone = bone_item[0]
                bpy.context.active_object.data.bones[bone].select = True
                if self.debug_output:
                    out = out + bone + " | "
                    
            if self.debug_output:
                print (str(frame), " Copy / Paste: ", out)
            bpy.ops.pose.copy()
            if self.append_mode:
                context.scene.frame_set(frame + self.append_frames_offset)
            bpy.ops.pose.paste(flipped = True)
            
    
    # Remove all those keyframes that have been marked for deletion
    def delete_unneeded_key_frames (self, context, delete_dict):
        for frame_item in delete_dict.items ():
            out = ""
            bpy.ops.pose.select_all(action='DESELECT')
            frame = frame_item[0]
            bones = frame_item[1]
            context.scene.frame_set(frame)
            has_keyframe_selected = False
            for bone_item in bones.items ():
                bone = bone_item[0]
                action = bone_item[1]
                if action == 'delete':
                    self.num_deleted += 1
                    has_keyframe_selected = True
                    bpy.context.active_object.data.bones[bone].select = True
                    if self.debug_output :
                        out = out + bone + " | "
                    
            if has_keyframe_selected:
                if self.debug_output:
                    print (str(frame), " Delete: ", out)
                bpy.ops.anim.keyframe_delete (type='Available',confirm_success=self.debug_output)
    
    
    def debug_print_keyframe_bone_dict (self):
        out = ""
        for frame in self.keyframe_bone_dict.items ():
            out = "[" + str(frame[0]) + "]: "
            for bone in frame[1].items ():
                out = out + str(bone[0]) + "=" + str(bone[1]) + " | "
            print (out)
    

def add_to_menu(self, context) :
    self.layout.operator("pose.flip_animation", icon = "PLUGIN")
 
def register() :
    bpy.types.Scene.flip_animation_append_mode = bpy.props.BoolProperty \
      (
        name = "Append Mode",
        description = "Copy all keyframes within the specified range and append them. Existing keyframes in the append range will be overwritten",
        default = False
      )
    bpy.types.Scene.flip_animation_start_frame = bpy.props.IntProperty \
      (
        name = "Start frame",
        description = "Start frame if checkbox 'Append Mode' is selected",
        default = 1
      )
    bpy.types.Scene.flip_animation_end_frame = bpy.props.IntProperty \
      (
        name = "End frame",
        description = "End frame if checkbox 'Append Mode' is selected",
        default = 10
      )
    bpy.utils.register_class(FlipAnimation)
    bpy.utils.register_class(FlipAnimationPanel)
    bpy.types.VIEW3D_MT_pose.append(add_to_menu)
 
def unregister() :
    bpy.utils.unregister_class(FlipAnimation)
    bpy.utils.unregister_class(FlipAnimationPanel)
    del bpy.types.Scene.flip_animation_append_mode
    del bpy.types.Scene.flip_animation_start_frame
    del bpy.types.Scene.flip_animation_end_frame
    bpy.types.VIEW3D_MT_pose.remove(add_to_menu)
 
if __name__ == "__main__" :
    register()
    

