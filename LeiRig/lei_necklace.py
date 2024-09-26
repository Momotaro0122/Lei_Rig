'''
Flower Lei Rig Setup.
Description:This tool create lei rig with flower collision from scratch.
Show: MAW
Rig System: None
Author: Martin Lee
Created: 8 Jun 2022
Last Updated: 14 Jun 2022 - Martin Lee
Usuage - Follow the hint on UI.
'''

import pymel.core as pm
import maya.cmds as mc
import maya.mel as mm
import maya.OpenMayaUI
import shiboken2
import PySide2.QtWidgets as qt
import PySide2.QtCore as qc
from functools import partial, reduce
from iRig.iRig_maya.lib import attrLib


# Functions.
def Create_Loc(target="test", suffix="PosLoc"):
    # ------create locator--------
    loc_name = "%s_%s" % (target, suffix)
    Loc = mc.spaceLocator(p=(0, 0, 0), n=loc_name)
    pCon = mc.parentConstraint(target, Loc, mo=0)
    mc.delete(pCon)
    mc.select(cl=True)

    return Loc


def Get_closest_point_cv(pos_loc, cv):
    npC = mc.createNode("nearestPointOnCurve")
    mc.connectAttr("%s.worldSpace" % (cv), npC + ".inputCurve")
    mc.connectAttr("%s.translate" % (pos_loc), npC + ".inPosition")
    # mc.setAttr(npC + ".inPosition", 1, 2, 3, type="double3")

    wsPos = mc.getAttr(npC + ".position")
    uParam = mc.getAttr(npC + ".parameter")

    mc.delete(npC)

    return wsPos, uParam


def get_main_window():
    main_window_ptr = maya.OpenMayaUI.MQtUtil.mainWindow()
    parent = shiboken2.wrapInstance(long(main_window_ptr), qt.QWidget)
    return parent


def reorder_list(target_list, move_back):
    # [1, 2, 3, 4, 5]
    # >>[2, 3, 4, 5, 1]
    if isinstance(target_list, list) and isinstance(move_back, int):
        if move_back > len(target_list):
            print("Please check your input, input int is greater then list.")
            return None

        new_ord_list = []
        for obj in target_list:
            new_ord_list.append(obj)
        for change in range(move_back):
            new_ord_list.append(new_ord_list[0])
            new_ord_list.pop(0)
        return new_ord_list
    else:
        return None


def Average(lst):
    return reduce(lambda a, b: a + b, lst) / len(lst)


def createJntCv(cLocator=False, cJoint=False, prefix="test", jointNum=20, sel=mc.ls(sl=True, l=True) or []):
    result_list = []
    averageLen = 1.0 / jointNum
    JntRename = "%s_jnt" % (prefix)
    if sel == []:
        cv = mc.curve(d=2, p=[(0, 0, 0), (5, 0, 0), (10, 0, 0)])
    else:
        cv = sel[0]
    # motion path
    firstCvPos = mc.xform(cv + ".cv" + "[" + str(0) + "]", ws=True, q=True, t=True)
    Ploc = mc.spaceLocator(p=(firstCvPos[0], firstCvPos[1], firstCvPos[2]))
    tmp_MP = mc.pathAnimation(Ploc[0], c=cv, su=0, eu=1)
    mc.setAttr(tmp_MP + ".fractionMode", 1)
    mc.select(cl=True)
    for jnt in range(jointNum):
        mc.setAttr(tmp_MP + '.uValue', averageLen * jnt)
        Tpos = mc.xform(Ploc, ws=True, q=True, t=True)
        if cLocator:
            tmp_loc = mc.spaceLocator(n="Lei_temp_%s_loc" % (jnt + 1))
            mc.move(
                Tpos[0],
                Tpos[1],
                Tpos[2], tmp_loc, absolute=True)
            mc.select(cl=True)
            result_list.append(tmp_loc[0])
        if cJoint:
            Jntcool = mc.joint(p=
                               (Tpos[0],
                                Tpos[1],
                                Tpos[2]), n=JntRename)
            mc.makeIdentity(Jntcool, apply=True)
            result_list.append(Jntcool[0])
    # if cJoint==True:
    #    mc.joint ("test_jnt",e=True,oj ='xyz',sao="zdown",ch=True,zso=True)
    mc.delete(Ploc, tmp_MP)
    return result_list


def create_ribbon_main_ctrl(tmp_loc):
    # Variable.
    all_main_ctrl_list = []
    # Create Ribbon Main ctrl grp.
    if pm.objExists("Lei_Main_Ctrl_Grp") == False:
        lei_main_ctrl_grp = pm.createNode("transform", n="Lei_Main_Ctrl_Grp")
    else:
        lei_main_ctrl_grp = pm.PyNode("Lei_Main_Ctrl_Grp")
    # Create Ribbon Main jnt grp.
    if pm.objExists("Lei_Main_Jnt_Grp") == False:
        lei_main_jnt_grp = pm.createNode("transform", n="Lei_Main_Jnt_Grp")
    else:
        lei_main_jnt_grp = pm.PyNode("Lei_Main_Jnt_Grp")

    for num in range(len(tmp_loc)):
        ctrl_name = "Lei_Main_%s" % (num + 1)
        main_ctrl = i_node.create("control", control_type="3D Cube", name=ctrl_name,
                                  color="green",
                                  gimbal_color="muddyGreen")
        all_main_ctrl_list.append(main_ctrl)
        gimbal = pm.PyNode("%s_Gimbal_Ctrl" % (ctrl_name))
        ctrl = pm.PyNode("%s_Ctrl" % (ctrl_name))
        offset_grp = pm.PyNode("%s_Ctrl_Offset_Grp" % (ctrl_name))
        # Move ctrl to loc pos.
        pm.delete(pm.pointConstraint(tmp_loc[num], offset_grp, mo=False))
        pm.delete(pm.orientConstraint(tmp_loc[num], offset_grp, mo=False))

        # Adjust ctrl shape.
        ctrl_cv = pm.NurbsCurveCV(ctrl, [cvNum for cvNum in range(16)])
        gimble_ctrl_cv = pm.NurbsCurveCV(gimbal, [cvNum for cvNum in range(16)])

        pm.scale(ctrl_cv, [12, 12, 12])
        pm.scale(gimble_ctrl_cv, [12, 12, 12])

        # main jnt creation.
        t_vert_pos = pm.xform(tmp_loc[num], ws=True, q=True, t=True)
        jnt = pm.joint(p=t_vert_pos, name="%s_Bnd_Jnt" % (ctrl_name))
        pm.select(cl=True)

        # main jnt offset.
        jnt_offset = pm.createNode("transform", n="%s_Jnt_Offset_Grp" % (ctrl_name))
        pm.delete(pm.pointConstraint(tmp_loc[num], jnt_offset, mo=False))
        pm.delete(pm.orientConstraint(tmp_loc[num], jnt_offset, mo=False))

        pm.parent(jnt, jnt_offset)
        pm.makeIdentity(jnt, a=True, r=True)
        pm.parent(offset_grp, lei_main_ctrl_grp)
        pm.parent(jnt_offset, lei_main_jnt_grp)

        # Parent constraint to jnt.
        pm.parentConstraint(gimbal, jnt_offset, mo=True)
        pm.scaleConstraint(gimbal, jnt_offset, mo=True)

    # delete pos_loc.
    for tmp in tmp_loc:
        pm.delete(tmp)
    return (all_main_ctrl_list, lei_main_ctrl_grp, lei_main_jnt_grp)


def create_jnt(jnt_vertx = 210):
    #try:
    # Variable.
    all_jnt_list = []
    all_jnt_offset_list = []
    object_list = []

    # Get selection data.
    selections = pm.ls(sl=True)
    selects = []
    for sel in selections:
        if ":" in sel:
            if sel.endswith("Geo"):
                filter = sel.split(":")[-1].replace("_Geo", "")
                selects.append(filter)
            else:
                filter = sel.split(":")[-1]
                selects.append(filter)
        else:
            if sel.endswith("Geo"):
                selects.append(sel.replace("_Geo", ""))
            else:
                selects.append(sel)
    pm.select(cl=True)
    print(selects)
    # print(sorted(selections))

    # Create Main jnt grp.
    if pm.objExists("Lei_Bnd_Jnt_Grp") == False:
        main_jnt_grp = pm.createNode("transform", n="Lei_Bnd_Jnt_Grp")
    else:
        main_jnt_grp = pm.PyNode("Lei_Bnd_Jnt_Grp")

    # Create joints by target vertex.
    for num, sel in enumerate(selections):
        if isinstance(sel, pm.nodetypes.Transform):
            target_vertex = pm.MeshVertex(sel, [jnt_vertx])
            t_vert_pos = pm.xform(target_vertex, ws=True, q=True, t=True)
            jnt = pm.joint(p=t_vert_pos, name="%s_Bnd_Jnt" % (selects[num]))
            pm.select(cl=True)
            object_list.append(sel)
            all_jnt_list.append(jnt)

        else:
            print("The object (%s) have no Transform Node!" % (sel))
            pass

    # Change list order for aim.
    new_ord_jnt_list = reorder_list(all_jnt_list, 1)

    # Make joints orient & add jnt offset grp.
    for aim_jnt, jnt in zip(new_ord_jnt_list, all_jnt_list):
        pm.delete(pm.aimConstraint(aim_jnt, jnt, mo=False))
        # Add offset grp.
        jnt_offset = pm.createNode("transform", n="%s_Offset_Grp" % (jnt))
        all_jnt_offset_list.append(jnt_offset)
        pm.delete(pm.pointConstraint(jnt, jnt_offset, mo=False))
        pm.delete(pm.orientConstraint(jnt, jnt_offset, mo=False))
        pm.parent(jnt, jnt_offset)
        pm.makeIdentity(jnt, a=True, r=True)
        pm.parent(jnt_offset, main_jnt_grp)
    for num, tar_jnt in enumerate(all_jnt_list):
        pm.skinCluster(tar_jnt, selections[num], tsb=True, mi=5)

    joint_result_list = (all_jnt_list, all_jnt_offset_list, main_jnt_grp, object_list)
    return joint_result_list
    #except:
    #    print("Create joints statement have some issues...")


def create_flower_ctrl(joint_result_list, control_shape="3D Cube", main_ctrl_color="aqua", gimbal_ctrl_color="red"):
    # Create Main ctrl grp.
    if pm.objExists("Lei_Flower_Ctrl_Grp") == False:
        main_ctrl_grp = pm.createNode("transform", n="Lei_Flower_Ctrl_Grp")
    else:
        main_ctrl_grp = pm.PyNode("Lei_Flower_Ctrl_Grp")
    # joint_result_list = (all_jnt_list, all_jnt_offset_list, main_jnt_grp, object_list)
    ctrl_name_list = []
    for sel in joint_result_list[-1]:
        if ":" in sel:
            if sel.endswith("Geo"):
                print("this geo have Geo suffix")
                filter = sel.split(":")[-1].replace("_Geo", "")
                ctrl_name_list.append(filter)
            else:
                print("no")
                filter = sel.split(":")[-1]
                ctrl_name_list.append(filter)
        else:
            if sel.endswith("Geo"):
                ctrl_name_list.append(sel.replace("_Geo", ""))
            else:
                ctrl_name_list.append(sel)
    #print(ctrl_name_list)

    for num, jnt in enumerate(joint_result_list[0]):
        i_node.create("control", control_type=control_shape, name=ctrl_name_list[num],
                      color=main_ctrl_color,
                      gimbal_color=gimbal_ctrl_color)

        offset_grp = pm.PyNode("%s_Ctrl_Offset_Grp" % (ctrl_name_list[num]))
        ctrl = pm.PyNode("%s_Ctrl" % (ctrl_name_list[num]))
        gimbal = pm.PyNode("%s_Gimbal_Ctrl" % (ctrl_name_list[num]))
        # Adjust ctrl shape.
        ctrl_cv = pm.NurbsCurveCV(ctrl, [cvNum for cvNum in range(8)])
        gimble_ctrl_cv = pm.NurbsCurveCV(gimbal, [cvNum for cvNum in range(8)])

        pm.rotate(ctrl_cv, [0, 0, 90])
        pm.rotate(gimble_ctrl_cv, [0, 0, 90])
        pm.scale(ctrl_cv, [5, 5, 5])
        pm.scale(gimble_ctrl_cv, [5, 5, 5])

        # Move ctrl to jnt pos.
        pm.delete(pm.pointConstraint(jnt, offset_grp, mo=False))
        pm.delete(pm.orientConstraint(jnt, offset_grp, mo=False))

        # Parent constraint to jnt.
        pm.parentConstraint(gimbal, joint_result_list[1][num], mo=True)
        pm.scaleConstraint(gimbal, joint_result_list[1][num], mo=True)

        pm.parent(offset_grp, main_ctrl_grp)


def flower_rig_setup():
    try:
        # Build jnts by sel.
        joint_result_list = create_jnt(jnt_vertx=geo_target_vetx.text())
        print(joint_result_list)
        # Create ctrl.
        create_flower_ctrl(joint_result_list, control_shape="2D Circle")
        print("Flower Rigs created!!!")
    except:
        print("Something wrong in flower_rig_setup statement, please check your selections and retry again...")


def create_main_ctrl(create_mctrl_num, create_mctrl_loc_btn=False, create_mctrl_btn=False):
    # Variables.
    avrg_x = []
    avrg_y = []
    avrg_z = []
    # Create temp loc step.
    if create_mctrl_loc_btn == True:
        LocNum = int(create_mctrl_num.text())
        # print(LocNum)
        #try:
        if isinstance(LocNum, int):
            target_cv = mc.ls(sl=True, l=True) or []
            global tmp_loc
            tmp_loc = createJntCv(cLocator=True, jointNum=LocNum, sel=target_cv)
            # Create Main Rig ctrl.
            # get tmp loc data.
            for i in tmp_loc:
                t_loc_pos = pm.xform(i, ws=True, q=True, t=True)
                avrg_x.append(t_loc_pos[0])
                avrg_y.append(t_loc_pos[1])
                avrg_z.append(t_loc_pos[2])
            x_average = Average(avrg_x)
            y_average = Average(avrg_y)
            z_average = Average(avrg_z)
            main_rig_loc = pm.spaceLocator(n="Lei_rig_main_temp_loc")
            pm.move(
                x_average,
                y_average,
                z_average, pm.PyNode("Lei_rig_main_temp_loc"), absolute=True)
            pm.select(cl=True)
        #except:
        #    print("The main ctrl number text input must be interger!!")
    # Create Main ctrl step.
    elif create_mctrl_btn == True:
        # print(tmp_loc)
        all_main_ctrl_list = create_ribbon_main_ctrl(tmp_loc)
        # return (all_main_ctrl_list, lei_main_ctrl_grp, lei_main_jnt_grp)
        if pm.objExists("Lei_Main_Rig_Ctrl_Offset_Grp") == False:
            main_ctrl = i_node.create("control", control_type="3D Cylinder", name="Lei_Main_Rig",
                                      color="yellow",
                                      gimbal_color="peach")
            pm.delete(pm.pointConstraint(pm.PyNode("Lei_rig_main_temp_loc"),
                                         pm.PyNode("%s_Ctrl_Offset_Grp" % ("Lei_Main_Rig")), mo=False))
            pm.delete(pm.orientConstraint(pm.PyNode("Lei_rig_main_temp_loc"),
                                          pm.PyNode("%s_Ctrl_Offset_Grp" % ("Lei_Main_Rig")), mo=False))
            pm.parent(pm.PyNode("%s_Ctrl_Offset_Grp" % ("Lei_Main_Rig")), all_main_ctrl_list[1])

            gimbal = pm.PyNode("%s_Gimbal_Ctrl" % ("Lei_Main_Rig"))
            ctrl = pm.PyNode("%s_Ctrl" % ("Lei_Main_Rig"))
            offset_grp = pm.PyNode("%s_Ctrl_Offset_Grp" % ("Lei_Main_Rig"))

            # Adjust ctrl shape.
            ctrl_cv = pm.NurbsCurveCV(ctrl, [cvNum for cvNum in range(32)])
            gimble_ctrl_cv = pm.NurbsCurveCV(gimbal, [cvNum for cvNum in range(32)])

            pm.scale(ctrl_cv, [47, 47, 47])
            pm.scale(ctrl_cv, [1, 0.01, 1])
            pm.scale(gimble_ctrl_cv, [47, 47, 47])
            pm.scale(gimble_ctrl_cv, [1, 0.01, 1])

            pm.delete(pm.PyNode("Lei_rig_main_temp_loc"))
            pm.select(cl=True)
            #print("Main ctrl created!!")


def create_close_cv_by_sel(curve_name = "Lei_cv"):
    t_list = []
    sel = mc.ls(sl=True, long=True)
    for i in sel:
        trans = mc.xform(i, ws=True, q=True, t=True)
        t_list.append(trans)
    cv = mc.curve(ep=t_list, d=3, n=curve_name)
    pm.closeCurve( cv, ch=True, ps=True ,rpo=True)
    print("Curve created!!")


def collision_setup():
    # Variables.
    Pos_Loc_list = []
    Aim_Loc_list = []
    target_driver_dict = {}

    # Select all flowers, then add select target curve.

    sel = mc.ls(sl=True)
    print(sel)
    obj_target = sel[0:-1]
    print(obj_target)
    cv = sel[-1]
    print(cv)

    # sel[0:-2] = all flower ctrls, sel[-1] = curve
    # Create Pos_Loc.
    if mc.objExists("Pos_Loc_Grp") == False:
        mc.createNode("transform", n="Pos_Loc_Grp")
    for i in obj_target:
        short_name = i.split("|")[-1]
        Pos_Loc = Create_Loc(target=short_name)
        mc.parent(Pos_Loc, "Pos_Loc_Grp")
        Temp_Loc = Create_Loc(target=short_name, suffix="TempLoc")
        # mo_path = mc.pathAnimation(Pos_Loc[0], c = cv, fm = True)
        mo_path = mm.eval(
            'pathAnimation -fractionMode false -follow true -followAxis x -upAxis y -worldUpType "vector" '
            '-worldUpVector 0 1 0 -inverseUp false -inverseFront false -bank false -startTimeU `playbackOptions '
            '-query -minTime` -endTimeU  `playbackOptions -query -maxTime`"%s" "%s";' % (cv, Pos_Loc[0]))
        wsPos, uParam = Get_closest_point_cv(Temp_Loc[0], cv)
        mm.eval('channelBoxCommand -break; CBdeleteConnection "%s.u";' % (mo_path))
        # mc.setAttr("%s.uValue"%(mo_path), uParam)
        mm.eval('setAttr "%s.uValue" %s;' % (mo_path, uParam))
        mc.delete(Temp_Loc)
        # build dict.
        target_driver_dict[i] = Pos_Loc
        Pos_Loc_list.append(Pos_Loc)

    # Parent constraints step.
    for target, driver in target_driver_dict.items():
        mc.pointConstraint(driver, target, mo=1)

    # Create Aim_Loc.
    if mc.objExists("Aim_Loc_Grp") == False:
        mc.createNode("transform", n="Aim_Loc_Grp")
    for obj in obj_target:
        short_name = obj.split("|")[-1]
        Aim_Loc = Create_Loc(target=short_name, suffix="AimLoc")
        Aim_Loc_list.append(Aim_Loc)
        mc.parent(Aim_Loc, "Aim_Loc_Grp")

    # Reorder Pos_Loc to do the blending aim constraint.
    new_ord_list = obj_target
    print(new_ord_list)
    for change in range(3):
        new_ord_list.append(new_ord_list[0])
        new_ord_list.pop(0)
    if pm.objExists("Lei_Main_Rig_Ctrl.collision") == False:
        collision_attr = pm.addAttr(pm.PyNode("%s_Ctrl" % ("Lei_Main_Rig")), longName="collision", at="bool", h=False,
                                    k=True, dv=1)
    else:
        collision_attr = "Lei_Rig_Main_Ctrl.collision"


    if pm.objExists("Lei_Main_Rig_Ctrl.collision"):
        # Blending aim constraint.
        for num, each in enumerate(new_ord_list):
            pointC = mc.pointConstraint(target_driver_dict[new_ord_list[num - 2]],
                                        target_driver_dict[new_ord_list[num - 1]], Aim_Loc_list[num], mo=0)

            mc.expression(s='''
            vector $A = {%s.translateX, %s.translateY, %s.translateZ};
            vector $B = {%s.translateX, %s.translateY, %s.translateZ};
            vector $C = {%s.translateX, %s.translateY, %s.translateZ};

            vector $AB = unit($B - $A);
            vector $BC = unit($C - $B);

            float $dotValue = dot($AB, $BC);

            if (Lei_Main_Rig_Ctrl.collision == true)
            {
                %s.%sW0 = max($dotValue, 0.5);
                %s.%sW1 = min(0.5, 1.0 - $dotValue);
            }
            else
            {
                %s.%sW0 = .7;
                %s.%sW1 = .3;
            }
            ''' % (target_driver_dict[new_ord_list[num - 3]][0], target_driver_dict[new_ord_list[num - 3]][0],
                   target_driver_dict[new_ord_list[num - 3]][0],
                   target_driver_dict[new_ord_list[num - 2]][0], target_driver_dict[new_ord_list[num - 2]][0],
                   target_driver_dict[new_ord_list[num - 2]][0],
                   target_driver_dict[new_ord_list[num - 1]][0], target_driver_dict[new_ord_list[num - 1]][0],
                   target_driver_dict[new_ord_list[num - 1]][0],
                   pointC[0], target_driver_dict[new_ord_list[num-2]][0],
                   pointC[0], target_driver_dict[new_ord_list[num-1]][0],
                   pointC[0], target_driver_dict[new_ord_list[num-2]][0],
                   pointC[0], target_driver_dict[new_ord_list[num-1]][0]))

            mc.aimConstraint(Aim_Loc_list[num], obj_target[num - 4], mo=1)
        print("Collision setup done!!!")
    else:
        mc.error(
            "The main rig ctrl don`t have attribute call .collision, check if there is any issues with the ctrl or it`s naming...")
    mc.select(cl=True)


def cleanup_connection(ctrl_num = 8):

    # Create Main ctrl grp.
    if pm.objExists("Lei_Rig_Grp") == False:
        main_ctrl_grp = pm.createNode("transform", n="Lei_Rig_Grp")
    else:
        main_def_grp = pm.PyNode("Lei_Rig_Grp")

    # Create lei def grp.
    if pm.objExists("Lei_Def_Grp") == False:
        main_def_grp = pm.createNode("transform", n="Lei_Def_Grp")
    else:
        main_ctrl_grp = pm.PyNode("Lei_Def_Grp")

    # Create Main ctrl grp.
    if pm.objExists("Lei_Jnt_Grp") == False:
        main_jnt_grp = pm.createNode("transform", n="Lei_Jnt_Grp")
    else:
        main_jnt_grp = pm.PyNode("Lei_Jnt_Grp")
    # Create Main ctrl grp.
    if pm.objExists("Lei_Ctrl_Grp") == False:
        lei_ctrl_grp = pm.createNode("transform", n="Lei_Ctrl_Grp")
    else:
        lei_ctrl_grp = pm.PyNode("Lei_Ctrl_Grp")


    for ctrl_count in range(1, int(ctrl_num) + 1):
        pm.parentConstraint(pm.PyNode("Lei_Main_Rig_Gimbal_Ctrl"),
                            pm.PyNode("Lei_Main_%s_Ctrl_Offset_Grp" % (ctrl_count)), mo=True)
        pm.scaleConstraint(pm.PyNode("Lei_Main_Rig_Gimbal_Ctrl"),
                           pm.PyNode("Lei_Main_%s_Ctrl_Offset_Grp" % (ctrl_count)), mo=True)
    # pm.PyNode(u'Rig_Info'),
    target_list = [pm.PyNode(u'Lei_Bnd_Jnt_Grp'),
                   pm.PyNode(u'Lei_Flower_Ctrl_Grp'),
                   pm.PyNode(u'Lei_cv'),
                   pm.PyNode(u'Lei_Main_Ctrl_Grp'),
                   pm.PyNode(u'Lei_Main_Jnt_Grp'),
                   pm.PyNode(u'Pos_Loc_Grp'),
                   pm.PyNode(u'Aim_Loc_Grp'),
                   pm.PyNode(u'Lei_Def_Grp'),
                   pm.PyNode(u'Lei_Jnt_Grp'),
                   pm.PyNode(u'Lei_Ctrl_Grp')]

    for tar in target_list:
        if pm.objExists(tar):
            # print("yes")
            pm.parent(tar, main_ctrl_grp)
        else:
            print("%s is not exist....Pass" % (tar))
            pass
    pm.select(cl=True)
    #move everthing in right spots.
    mc.parent("Lei_Bnd_Jnt_Grp", "Lei_Jnt_Grp")
    mc.parent("Lei_Main_Jnt_Grp", "Lei_Jnt_Grp")
    mc.parent("Lei_cv", "Lei_Def_Grp")
    mc.parent("Pos_Loc_Grp", "Lei_Def_Grp")
    mc.parent("Aim_Loc_Grp", "Lei_Def_Grp")
    mc.parent("Lei_Main_Ctrl_Grp", "Lei_Ctrl_Grp")
    mc.parent("Lei_Flower_Ctrl_Grp", "Lei_Ctrl_Grp")

    #Flower each vis toggle.
    attrLib.addFloat('Lei_Main_Rig_Ctrl', ln='TweakVis', min=0, max=1, v=0)
    mc.connectAttr("Lei_Main_Rig_Ctrl.TweakVis", "Lei_Flower_Ctrl_Grp.v")
    pm.select(cl=True)
    print("Cleanup & Connected!!!")


def main_win():
    for widget in qt.QApplication.allWidgets():
        if widget.objectName() == "fl_win":
            widget.deleteLater()
    # ===============window========================
    flower_setup_window = qt.QWidget()
    flower_setup_window.setObjectName("fl_win")
    flower_setup_window.resize(250, 75)
    flower_setup_window.setWindowTitle('Flower Rig setup window')
    flower_setup_layout = qt.QVBoxLayout(flower_setup_window)

    mctrl_widget = qt.QWidget()
    mctrl_layout = qt.QHBoxLayout(mctrl_widget)
    # ===============items=====================
    fl_setup_hint_lb = qt.QLabel("Select all flowers geo by order...\n This will create ctrl and jnt on each flower.")
    create_mctrl_loc_lb = qt.QLabel("Select target curve and hit this button...\n "
                                    "This will create temp loc (move it to proper place) for main ctrl.")
    create_mctrl_lb = qt.QLabel(
        "Hit this button after move the temp loc to proper place...\n This will create main ctrls base on temp loc.")
    create_close_cv_by_sel_lb = qt.QLabel("Select flower ctrl offset grp or jnt, ctrl..etc to create close curve\n "
                                          "Ex.Flower_000*_Geo_Ctrl_Offset_Grp...")
    collsion_setup_lb = qt.QLabel("Select flower ctrl offset grp then add select the curve.")
    cleanup_connection_lb = qt.QLabel("Hit this button for cleanup the lei rig grp in the scene and \n"
                                      "connect main rig ctrl to main ctrl.")

    create_mctrl_num_lb = qt.QLabel("Main ctrl number")
    create_mctrl_num = qt.QLineEdit("8")

    geo_target_vetx = qt.QLineEdit("210")

    fl_setup_hint_btn = qt.QPushButton('Flower Rig Setup \(>_<)')
    create_mctrl_loc_btn = qt.QPushButton('Create Temp Loc (O3O)')
    create_mctrl_btn = qt.QPushButton('Create Main Ctrl (0.0);')
    create_close_cv_by_sel_btn = qt.QPushButton("Create Close Curve By Selections ($3$)/")
    collsion_setup_btn = qt.QPushButton("Collision Setup \(0.0)/")
    cleanup_connection_btn = qt.QPushButton("Cleanup & Connected <(c_c)< ")

    create_mctrl_loc_btn.setObjectName("mctrl_loc_btn")
    create_mctrl_btn.setObjectName("mctrl_btn")
    # ===============events=====================

    fl_setup_hint_btn.setStyleSheet('background-color : orange; color : black')
    fl_setup_hint_btn.clicked.connect(partial(flower_rig_setup))
    create_mctrl_loc_btn.setStyleSheet('background-color : blue')
    create_mctrl_loc_btn.clicked.connect(partial(create_main_ctrl, create_mctrl_num, create_mctrl_loc_btn=True))
    create_mctrl_btn.setStyleSheet('background-color : purple')
    create_mctrl_btn.clicked.connect(partial(create_main_ctrl, create_mctrl_num, create_mctrl_btn=True))

    create_close_cv_by_sel_btn.setStyleSheet('background-color : green')
    create_close_cv_by_sel_btn.clicked.connect(partial(create_close_cv_by_sel))
    collsion_setup_btn.setStyleSheet('background-color : pink; color : black')
    collsion_setup_btn.clicked.connect(partial(collision_setup))
    cleanup_connection_btn.setStyleSheet('background-color : gold; color : black')
    cleanup_connection_btn.clicked.connect(partial(cleanup_connection, ctrl_num = create_mctrl_num.text()))
    # btn.keyReleaseEvent.connect(partial(renameTool,txt))
    # txt.returnPressed.connect(partial(renameTool,txt))

    # ============layouts&widgets=====================
    flower_setup_layout.addWidget(fl_setup_hint_lb)
    flower_setup_layout.addWidget(geo_target_vetx)
    flower_setup_layout.addWidget(fl_setup_hint_btn)
    flower_setup_layout.addWidget(create_close_cv_by_sel_lb)
    flower_setup_layout.addWidget(create_close_cv_by_sel_btn)
    flower_setup_layout.addWidget(create_mctrl_loc_lb)
    mctrl_layout.addWidget(create_mctrl_num_lb)
    mctrl_layout.addWidget(create_mctrl_num)
    flower_setup_layout.addWidget(mctrl_widget)
    flower_setup_layout.addWidget(create_mctrl_loc_btn)
    flower_setup_layout.addWidget(create_mctrl_lb)
    flower_setup_layout.addWidget(create_mctrl_btn)
    flower_setup_layout.addWidget(collsion_setup_lb)
    flower_setup_layout.addWidget(collsion_setup_btn)
    flower_setup_layout.addWidget(cleanup_connection_lb)
    flower_setup_layout.addWidget(cleanup_connection_btn)

    # ============WindowShow=====================
    # parent maya main window
    main_window = get_main_window()
    flower_setup_window.setParent(main_window)
    flower_setup_window.setWindowFlags(qc.Qt.Window)

    flower_setup_window.show()