import bpy, json
print(json.dumps({'blender_version':bpy.app.version_string,'binary':bpy.app.binary_path,'filepath':bpy.data.filepath,'dirty':bpy.data.is_dirty,'active_scene':bpy.context.scene.name,'scenes':[{'name':s.name,'objects':len(s.objects)} for s in bpy.data.scenes],'render_engines':[x.identifier for x in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]}))
