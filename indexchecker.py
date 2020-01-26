import bpy,bmesh
from bpy.props import BoolProperty, PointerProperty
import blf
import bpy_extras.view3d_utils

bl_info = {
    "name": "indexChecker",
    "author": "katsumi",
    "version": (1, 0),
    "blender": (2, 81, 0),
    "location": "3Dビュー > プロパティパネル > IDを表示",
    "description": "オブジェクトの頂点・辺・面のIDを描画するアドオン",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"
}

translation_dict = {
    "en_US" :
        {("*", "Display index") : "Display index",
        ("*", "start") : "start",
         ("*", "stop") : "stop"},
         
    "ja_JP" :
        {("*", "Display index") : "indexを表示",
         ("*", "start") : "開始",
         ("*", "stop") : "終了"
         }}
# ------------------------------------------------------------------------
#   operator  buttun
# ------------------------------------------------------------------------
class Render_OT_Text(bpy.types.Operator):

    bl_idname = "view_3d.render_text"
    bl_label = "indexを表示"
    bl_description = "indexを表示します"

    __handle = None           # 描画関数ハンドラ

    def __handle_add(self, context):
        if Render_OT_Text.__handle is None:
            # 描画関数の登録
            Render_OT_Text.__handle = bpy.types.SpaceView3D.draw_handler_add(
                Render_OT_Text.__render, (self, context), 'WINDOW', 'POST_PIXEL')


            

    def __handle_remove(self, context):
        if Render_OT_Text.__handle is not None:
            # 描画関数の登録を解除
            bpy.types.SpaceView3D.draw_handler_remove(
                Render_OT_Text.__handle, 'WINDOW'
            )
            Render_OT_Text.__handle = None

    @staticmethod
    def __render_text(size, x, y, s ):
        # フォントサイズを指定
        blf.size(0, size, size)
        # 描画位置を指定
        blf.position(0, x, y, 0)
        # テキストを描画
        blf.draw(0, s)      

    @staticmethod
    def __get_region(context, area_type, region_type):
        region = None
        area = None

        # 指定されたエリアを取得する
        for a in context.screen.areas:
            if a.type == area_type:
                area = a
                break
        else:
            return None
        # 指定されたリージョンを取得する
        for r in area.regions:
            if r.type == region_type:
                region = r
                break

        return region

    @staticmethod
    def __render(self, context):
        if bpy.context.mode != "EDIT_MESH":
            #開始途中でオブジェクトモードにした時にblender停止を防ぎボタンを開始に戻す
            sc = context.scene
            sc.rt_running = False
            context.area.tag_redraw()
            return
        if len(bpy.context.space_data.region_quadviews):
            return 
        obj = bpy.context.view_layer.objects.active
        bpy.ops.object.mode_set(mode='EDIT')
        bm: bmesh.types.BMesh = bmesh.from_edit_mesh(obj.data)
        r = bpy.context.region
        rv3d = bpy.context.space_data.region_3d
        for i in bm.verts:
            if i.select:
                p = bpy_extras.view3d_utils.location_3d_to_region_2d(
                    r, rv3d, obj.matrix_world @ i.co)
                if p is not None:
                    Render_OT_Text.__render_text(
                    30, p.x, p.y, f"{i.index}"
                )
        for i in bm.edges:
            if i.select:
                cn = (i.verts[0].co+i.verts[1].co)/2
                p = bpy_extras.view3d_utils.location_3d_to_region_2d(
                    r, rv3d, obj.matrix_world @ cn)
                if p is not None:
                    Render_OT_Text.__render_text(
                    30, p.x, p.y, f"{i.index}"
                    )  
        for i in bm.faces:
            if i.select:
                cn = i.calc_center_median()
                p = bpy_extras.view3d_utils.location_3d_to_region_2d(
                    r, rv3d, obj.matrix_world @ cn)
                if p is not None:
                    Render_OT_Text.__render_text(
                    30, p.x, p.y, f"{i.index}"
                    )
    
    
    def invoke(self, context, event):
        sc = context.scene
        if context.area.type == 'VIEW_3D':
            #obj_mode = bpy.context.mode
            # 開始ボタンが押された時の処理
            if sc.rt_running is False:
                global obj_mode 
                obj_mode = bpy.context.mode
                if obj_mode != "EDIT_MESH":
                    bpy.ops.object.mode_set(mode='EDIT')
                sc.rt_running = True
                self.__handle_add(context)
                print("indexの表示を開始しました。")
            # 終了ボタンが押された時の処理
            else:
                if obj_mode != "EDIT_MESH":
                    bpy.ops.object.mode_set(mode='OBJECT')
                sc.rt_running = False
                self.__handle_remove(context)
                print("indexの表示を終了しました。")
            # 3Dビューの画面を更新
            if context.area:
                context.area.tag_redraw()
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

# ------------------------------------------------------------------------
#   addon - panel -- visible in objectmode
# ------------------------------------------------------------------------
class OBJECT_PT_RT(bpy.types.Panel):
#
    bl_label = bpy.app.translations.pgettext("Display index")
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
#
    def draw(self, context):
        sc = context.scene
        layout = self.layout
        # 開始/停止ボタンを追加
        if sc.rt_running is False:
            layout.operator(Render_OT_Text.bl_idname, text=bpy.app.translations.pgettext("start"), icon="PLAY")
        else:
            layout.operator(Render_OT_Text.bl_idname, text=bpy.app.translations.pgettext("stop"), icon="PAUSE")


# プロパティの作成
def init_props():
    sc = bpy.types.Scene
    sc.rt_running = BoolProperty(
        name="実行中",
        description="実行中か？",
        default=False
    )


# プロパティの削除
def clear_props():
    sc = bpy.types.Scene
    del sc.rt_running


# ------------------------------------------------------------------------
# register and unregister
# ------------------------------------------------------------------------

def register():    
    bpy.app.translations.register(__name__, translation_dict)
    bpy.utils.register_class(OBJECT_PT_RT)
    bpy.utils.register_class(Render_OT_Text)
    init_props()
    
    print("アドオン「indexChecker」が有効化されました。")


def unregister():
    clear_props()
    bpy.utils.unregister_class(Render_OT_Text)
    bpy.utils.unregister_class(OBJECT_PT_RT)
    bpy.app.translations.unregister(__name__)
    print("アドオン「indexChecker」が無効化されました。")


if __name__ == "__main__":
    register()