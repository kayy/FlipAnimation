FlipAnimation add-on for Blender (version > 2.58)
Author Kay Bothfeld, SCIO System-Consulting GmbH & Co.KG

Download:
http://files.scio.de/blog/FlipAnimation/FlipAnimation.zip

Documentation:
http://www.scio.de/en/blog-a-news/scio-development-blog-en/entry/flip-animation-add-on-for-mirroring-keyframes-in-blender

Tested on Mac OSX, Blender 2.58 and Linux with Blender 2.66

Quick instructions:
- Download
- Install via User Preferences / Add-Ons / Install Add-On
- Go to Pose Mode
- Select an action
- Ensure that button 'Automatic Keyframe Insertion for Objects And Bones' in timeline view is pressed
- Ensure that button 'Automatic Keyframe Insertion Using Active Keying Set Only' in timeline view is pressed
- In 3D view look for a panel called 'Flip Animation' in Tool shelf (T)
- Press button 'Flip Animation' to mirror the whole action currently selected
- Check 'Append Mode', specify the range to flip and press 'Flip Animation' to get a mirrored copy the range appended
  after the last frame


Troubleshooting:

- Check that your bones conform to Blender's bone naming conventions. That means suffix _ or . and then R / L, r / l, 
  right / left, Right / Left. Alternatively you can use them as prefix in similar way.
  Examples: Hand_R, Hand.r, Hand.Right, É or R_Hand, r.Hand, Right.Hand
- Does the current keying set contain all relevant channels? For example check that you selected LocRotScale if your 
  keyframes define location, rotation and scaling changes
- If the start or end frame is outside of the defined range of the action, the add-on shows a warning messages in the 
  status field of the info menu
- Note that all existing keyframes within the range needed for appending, are overwritten.
  If we for example specify the range  1-5 all frames between 6 and 10 are deleted and the flipped keyframes are 
  inserted instead
- As the code relies on the Blender operators for copy pose and  Past X-Flipped Pose it needs some preconditions.
- There is a button in Timeline View to enable Automatic Keyframe Insertion for Objects And Bones. This little red 
  recording icon. This needs to be enabled. If it's deactivated, a warning message shows up.
- The same applies for other button right to it called Automatic Keyframe Insertion Using Active Keying Set Only
- The keying set to use for inserting and deleting keyframes set right here, should fit the needs of your action. 
  In most cases Available should be a good choice. If you have keyframes containing Location and Rotation values but 
  have configured Location only as active keying set, pasting will not consider your rotation keys.
- Sometimes pasting X-flipped poses lead to kind of weird results. I had this occasionally before I developed the 
  add-on and noticed some issues within the quaternions as the inversion did not perform right. Maybe this is solved 
  in the meantime. If you have this problem at one single bone, just modify the rotation slightly and it might disappear.

     
Developer info:

- For debugging set debug_output = True at the beginning of class FlipAnimation and start Blender from terminal to 
  see output

