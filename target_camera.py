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

import bpy, math
from utils import *

targetCameraName = "TARGET CAMERA"
movementEmptyName = "MOVEMENT"
dataEmptyName = "TARGET CAMERA CONTAINER"
strongWiggleEmptyName = "STRONG WIGGLE"
wiggleEmptyName = "WIGGLE"
distanceEmptyName = "DISTANCE"
focusEmptyName = "FOCUS"
realTargetPrefix = "REAL TARGET"
travelPropertyName = "travel"
wiggleStrengthPropertyName = "wiggle strength"
partOfTargetCamera = "part of target camera"
deleteOnRecalculation = "delete on recalculation"

travelDataPath = '["' + travelPropertyName + '"]'
wiggleStrengthDataPath = '["' + wiggleStrengthPropertyName + '"]'

useListSeparator = False

oldHash = ""


# insert basic camera setup
#################################

def insertTargetCamera():
	oldSelection = getSelectedObjects()
	removeOldTargetCameraObjects()

	camera = newCamera()
	focus = newFocusEmpty()
	movement = newMovementEmpty()
	distanceEmpty = newDistanceEmpty()
	strongWiggle = newStrongWiggleEmpty()
	wiggle = newWiggleEmpty()
	dataEmpty = newDataEmpty()
	
	focus.parent = dataEmpty
	movement.parent = dataEmpty
	distanceEmpty.parent = movement
	strongWiggle.parent = distanceEmpty
	wiggle.parent = distanceEmpty
	camera.parent = wiggle;
	
	distanceEmpty.location.z = 4
	
	setActive(camera)
	bpy.context.object.data.dof_object = focus
	
	insertWiggleConstraint(wiggle, strongWiggle, dataEmpty)
	
	setSelectedObjects(oldSelection)
	newTargets()
	
def removeOldTargetCameraObjects():
	for object in bpy.context.scene.objects:
		if isPartOfTargetCamera(object):
			delete(object)
	
def newCamera():
	bpy.ops.object.camera_add(location = [0, 0, 0])
	camera = bpy.context.object
	camera.name = targetCameraName
	camera.rotation_euler = [0, 0, 0]
	makePartOfTargetCamera(camera)
	bpy.context.scene.camera = camera
	return camera
	
def newFocusEmpty():
	focus = newEmpty(name = focusEmptyName, location = [0, 0, 0])
	focus.empty_draw_size = 0.2
	makePartOfTargetCamera(focus)
	focus.hide = True
	return focus
	
def newMovementEmpty():
	movement = newEmpty(name = movementEmptyName, location = [0, 0, 0])
	movement.empty_draw_size = 0.2
	makePartOfTargetCamera(movement)
	movement.hide = True
	return movement
	
def newDistanceEmpty():
	distanceEmpty = newEmpty(name = distanceEmptyName, location = [0, 0, 0])
	distanceEmpty.empty_draw_size = 0.2
	makePartOfTargetCamera(distanceEmpty)
	distanceEmpty.hide = True
	return distanceEmpty

def newStrongWiggleEmpty():
	strongWiggle = newEmpty(name = strongWiggleEmptyName, location = [0, 0, 0])
	strongWiggle.empty_draw_size = 0.2
	makePartOfTargetCamera(strongWiggle)
	strongWiggle.hide = True
	return strongWiggle
	
def newWiggleEmpty():
	wiggle = newEmpty(name = wiggleEmptyName, location = [0, 0, 0])
	wiggle.empty_draw_size = 0.2
	makePartOfTargetCamera(wiggle)
	wiggle.hide = True
	return wiggle

def newDataEmpty():
	dataEmpty = newEmpty(name = dataEmptyName, location = [0, 0, 0])
	setCustomProperty(dataEmpty, travelPropertyName, 1.0, min = 1.0)
	setCustomProperty(dataEmpty, "stops", [])
	setCustomProperty(dataEmpty, wiggleStrengthPropertyName, 0.0, min = 0.0, max = 1.0)
	setCustomProperty(dataEmpty, "wiggle scale", 5.0, min = 0.0)
	dataEmpty.hide = True
	lockCurrentTransforms(dataEmpty)
	makePartOfTargetCamera(dataEmpty)
	return dataEmpty

def insertWiggleConstraint(wiggle, strongWiggle, dataEmpty):
	constraint = wiggle.constraints.new(type = "COPY_TRANSFORMS")
	constraint.target = strongWiggle
	driver = newDriver(wiggle, 'constraints["' + constraint.name + '"].influence')
	linkFloatPropertyToDriver(driver, "var", dataEmpty, wiggleStrengthDataPath)	
	driver.expression = "var**2"
	
# create animation
###########################

def recalculateAnimation():
	createFullAnimation(getTargetList())
	
def createFullAnimation(targetList):
	global oldHash
	cleanupScene(targetList)
	removeAnimation()

	movement = getMovementEmpty()
	focus = getFocusEmpty()
	dataEmpty = getDataEmpty()
	deleteAllConstraints(movement)
	deleteAllConstraints(focus)
	
	createWiggleModifiers()
	
	for i in range(len(targetList)):
		target = targetList[i]
		if i == 0: targetBefore = target
		else: targetBefore = targetList[i-1]
		
		(base, emptyAfter) = createInertiaEmpties(target, targetBefore)
		createConstraintSet(movement, base)
		createConstraintSet(focus, getTargetObjectFromTarget(base))
		
	createTravelToConstraintDrivers(movement)
	createTravelToConstraintDrivers(focus)	
	createTravelAnimation(targetList)
	calculatedTargetAmount = getTargetAmount()
	
	oldHash = getCurrentSettingsHash()
	
def cleanupScene(targetList):
	oldSelection = getSelectedObjects()
	for object in bpy.context.scene.objects:
		if isTargetName(object.name) and object not in targetList or isDeleteOnRecalculation(object):
			oldSelection = [x for x in oldSelection if x != object]
			delete(object)	
	setSelectedObjects(oldSelection)
	
def removeAnimation():
	clearAnimation(getDataEmpty(), travelDataPath)
	
def createInertiaEmpties(target, before):
	base = newEmpty(name = "base", type = "SPHERE")
	base.empty_draw_size = 0.15
	
	emptyAfter = newEmpty(name = "after inertia")
	emptyAfter.empty_draw_size = 0.1
	
	setParentWithoutInverse(base, target)
	setParentWithoutInverse(emptyAfter, base)
	
	makeDeleteOnRecalculation(base)
	makeDeleteOnRecalculation(emptyAfter)
	
	createPositionConstraint(emptyAfter, target, before)
	return (base, emptyAfter)
def createPositionConstraint(emptyAfter, target, before):
	constraint = emptyAfter.constraints.new(type = "LIMIT_LOCATION")
	constraint.use_min_x = True
	constraint.use_max_x = True
	constraint.use_min_y = True
	constraint.use_max_y = True
	constraint.use_min_z = True
	constraint.use_max_z = True

	distance = 1
	
	driver = newDriver(emptyAfter, 'constraints["' + constraint.name + '"].min_x')
	linkVariablesToIntertiaDriver(driver, target, before)
	driver.expression = "(x1-x2)/(sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)+0.000001) * "+ str(distance) +"+x1"	
	createCopyValueDriver(emptyAfter, 'constraints["' + constraint.name + '"].min_x', emptyAfter, 'constraints["' + constraint.name + '"].max_x')
	
	driver = newDriver(emptyAfter, 'constraints["' + constraint.name + '"].min_y')
	linkVariablesToIntertiaDriver(driver, target, before)
	driver.expression = "(y1-y2)/(sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)+0.000001) * "+ str(distance) +"+y1"
	createCopyValueDriver(emptyAfter, 'constraints["' + constraint.name + '"].min_y', emptyAfter, 'constraints["' + constraint.name + '"].max_y')
	
	driver = newDriver(emptyAfter, 'constraints["' + constraint.name + '"].min_z')
	linkVariablesToIntertiaDriver(driver, target, before)
	driver.expression = "(z1-z2)/(sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)+0.000001) * "+ str(distance) +"+z1"
	createCopyValueDriver(emptyAfter, 'constraints["' + constraint.name + '"].min_z', emptyAfter, 'constraints["' + constraint.name + '"].max_z')
	
	
def linkVariablesToIntertiaDriver(driver, target, before):
	linkTransformChannelToDriver(driver, "x1", target, "LOC_X")
	linkTransformChannelToDriver(driver, "x2", before, "LOC_X")
	linkTransformChannelToDriver(driver, "y1", target, "LOC_Y")
	linkTransformChannelToDriver(driver, "y2", before, "LOC_Y")
	linkTransformChannelToDriver(driver, "z1", target, "LOC_Z")
	linkTransformChannelToDriver(driver, "z2", before, "LOC_Z")
	
def createWiggleModifiers():
	global oldWiggleScale
	strongWiggle = getStrongWiggle()
	dataEmpty = getDataEmpty()
	wiggleScale = getWiggleScale(dataEmpty)
	clearAnimation(strongWiggle, "location")
	strongWiggle.location = [0, 0, 0]
	insertWiggle(strongWiggle, "location", 6, wiggleScale)
	oldWiggleScale = wiggleScale
	
def createConstraintSet(object, target):
	constraint = object.constraints.new(type = "COPY_TRANSFORMS")
	constraint.target = target
	constraint.influence = 0
	constraint.show_expanded = False
	
def createTravelToConstraintDrivers(object):
	dataEmpty = getDataEmpty()
	constraints = object.constraints
	for i in range(getTargetAmount()):
		constraint = constraints[i]
		driver = newDriver(object, 'constraints["' + constraint.name + '"].influence')
		linkFloatPropertyToDriver(driver, "var", dataEmpty, travelDataPath)
		driver.expression = "var - " + str(i)
		
def createTravelAnimation(targetList):
	dataEmpty = getDataEmpty()
	stops = []
	
	frame = 0
	for i in range(getTargetAmount()):
		frame += getLoadingTime(targetList[i])
		dataEmpty[travelPropertyName] = float(i + 1)
		dataEmpty.keyframe_insert(data_path=travelDataPath, frame = frame)
		stops.append(frame)
		
		frame += getStayTime(targetList[i])
		dataEmpty[travelPropertyName] = float(i + 1)
		dataEmpty.keyframe_insert(data_path=travelDataPath, frame = frame)
	setStops(dataEmpty, stops)
		
	positionKeyframeHandles(targetList)
			
def positionKeyframeHandles(targetList):
	dataEmpty = getDataEmpty()
	changeHandleTypeOfAllKeyframes(dataEmpty, travelDataPath, "FREE")
	keyframes = getKeyframePoints(dataEmpty, travelDataPath)
	if len(keyframes) >= 2:
		for i in range(len(keyframes)):
			keyframe = keyframes[i]
			sourceX = keyframe.co.x
			sourceY = keyframe.co.y
			if i > 0:
				beforeX = keyframes[i-1].co.x
				beforeY = keyframes[i-1].co.y
			else:
				beforeX = sourceX
				beforeY = sourceY
			if i < len(keyframes) - 1: 
				afterX = keyframes[i+1].co.x
				afterY = keyframes[i+1].co.y
			else:
				afterX = sourceX
				afterY = sourceY
				
			(easyIn, strengthIn, easyOut, strengthOut) = getInterpolationParameters(targetList[int(sourceY) - 1])
			keyframe.handle_left.x = (beforeX - sourceX) * easyIn * strengthIn + sourceX
			keyframe.handle_left.y = (beforeY - sourceY) * (1 - easyIn) * strengthIn + sourceY				
			keyframe.handle_right.x = (afterX - sourceX) * easyOut * strengthOut + sourceX
			keyframe.handle_right.y = (afterY - sourceY) * (1 - easyOut) * strengthOut + sourceY
			
		
def getInterpolationParameters(target):
	target["easy in"] = clamp(target["easy in"], 0.0, 1.0)
	target["easy out"] = clamp(target["easy out"], 0.0, 1.0)
	(easyIn, influenceIn) = getInterpolationParametersFromSingleValue(target["easy in"])
	(easyOut, influenceOut) = getInterpolationParametersFromSingleValue(target["easy out"])
	return (easyIn, influenceIn, easyOut, influenceOut)
	
def getInterpolationParametersFromSingleValue(easyValue):
	easyValue = clamp(easyValue, 0, 1)
	if easyValue < 0.2:
		easy = 0
		influence = 0.5 + (0.2 - easyValue) * 2.5
	elif easyValue > 0.8:
		easy = 1
		influence = 0.5 + (easyValue - 0.8) * 2.5
	else:
		easy = (easyValue - 0.2) * 5 / 3
		influence = 0.5
	return (easy, influence)
	
# target operations
#############################

def newTargets():
	targets = getTargetList()
	selectedObjects = []
	for object in getSelectedObjects():
		if not (object == getTargetCamera() or object == getMovementEmpty()):
			selectedObjects.append(object)
		
	selectedObjects.reverse()
	for object in selectedObjects:
		targets.append(newRealTarget(object))
	createFullAnimation(targets)
	
def newRealTarget(target):
	if isValidTarget(target): return target
	
	deselectAll()
	setActive(target)
	bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY')

	empty = newEmpty(name = realTargetPrefix, location = [0, 0, 0])
	empty.empty_draw_size = 0.4
	setParentWithoutInverse(empty, target)
	
	setCustomProperty(empty, "loading time", 25, min = 1)
	setCustomProperty(empty, "stay time", 20, min = 0)
	setCustomProperty(empty, "easy in", 0.8, min = 0.0, max = 1.0)
	setCustomProperty(empty, "easy out", 0.8, min = 0.0, max = 1.0)
	
	makePartOfTargetCamera(empty)
	
	return empty
	
def deleteTarget(index):
	targets = getTargetList()
	del targets[index]
	createFullAnimation(targets)
	
def moveTargetUp(index):
	if index > 0:
		targets = getTargetList()
		targets.insert(index-1, targets.pop(index))
		createFullAnimation(targets)
def moveTargetDown(index):
	targets = getTargetList()
	targets.insert(index+1, targets.pop(index))
	createFullAnimation(targets)
	
def goToNextTarget():
	travel = getTravelValue()
	newTravel = math.floor(travel) + 1
	bpy.context.screen.scene.frame_current = getFrameOfTravelValue(newTravel)
def goToPreviousTarget():
	travel = getTravelValue()
	newTravel = math.ceil(travel) - 1
	bpy.context.screen.scene.frame_current = getFrameOfTravelValue(newTravel)
	
def getFrameOfTravelValue(travel):
	travel = max(1, travel)
	stops = getDataEmpty()['stops']
	if len(stops) > 0:
		if travel >= len(stops):
			return stops[-1]
		else:
			return stops[int(travel - 1)]
	else: return 1
	
def copyInterpolationProperties(index):
	targets = getTargetList()
	sourceTarget = targets[index]
	easyIn = sourceTarget["easy in"]
	easyOut = sourceTarget["easy out"]
	for target in targets:
		target["easy in"] = easyIn
		target["easy out"] = easyOut
	recalculateAnimation()
	
	
# utilities
#############################

def targetCameraExists():
	if getTargetCamera() is None: return False
	else: return True
def isTargetCamera(object):
	return object.name == targetCameraName
	
	
def getTargetCamera():
	return bpy.data.objects.get(targetCameraName)
def getFocusEmpty():
	return bpy.data.objects.get(focusEmptyName)
def getMovementEmpty():
	return bpy.data.objects.get(movementEmptyName)
def getDataEmpty():
	return bpy.data.objects.get(dataEmptyName)
def getStrongWiggle():
	return bpy.data.objects.get(strongWiggleEmptyName)
	
	
def selectTargetCamera():
	camera = getTargetCamera()
	if camera:
		deselectAll()
		camera.select = True
		setActive(camera)
def selectMovementEmpty():
	deselectAll()
	setActive(getMovementEmpty())
def selectTarget(index):
	deselectAll()
	target = getTargetList()[index]
	setActive(target)
		
		
def getTargetAmount():
	return len(getTargetList())
def getTargetList():
	targets = []
	uncleanedTargets = getUncleanedTargetList()
	for target in uncleanedTargets:
		if isValidTarget(target) and target not in targets:
			targets.append(target)
	return targets
def getUncleanedTargetList():
	constraintTargets = getConstraintTargetList()
	uncleanedTargets = []
	for constraintTarget in constraintTargets:
		if hasattr(constraintTarget, "parent"):
			uncleanedTargets.append(constraintTarget.parent)
	return uncleanedTargets
def getConstraintTargetList():
	movement = getMovementEmpty()
	constraintTargets = []
	for constraint in movement.constraints:
		if hasattr(constraint, "target"):
			constraintTargets.append(constraint.target)
	return constraintTargets
def isValidTarget(target):
	if hasattr(target, "name"):
		if isTargetName(target.name):
			if hasattr(target, "parent"):
				if hasattr(target.parent, "name"):
					return True
	return False
def isTargetName(name):
	return name[:len(realTargetPrefix)] == realTargetPrefix
	
def getTargetObjectFromTarget(target):
	return target.parent
def getSelectedTargets(targetList):
	objects = getSelectedObjects()
	targets = []
	for object in objects:
		targetsOfObject = getTargetsFromObject(object, targetList)
		for target in targetsOfObject:
			if target not in targets:
				targets.append(target)
	return targets
def getTargetsFromObject(object, targetList):
	targets = []
	if isValidTarget(object): targets.append(object)
	for target in targetList:
		if target.parent.name == object.name: targets.append(target)
	return targets
	
	
def makePartOfTargetCamera(object):
	object[partOfTargetCamera] = "1"
def isPartOfTargetCamera(object):
	if object.get(partOfTargetCamera) is None:
		return False
	return True
def makeDeleteOnRecalculation(object):
	object[deleteOnRecalculation] = "1"
def isDeleteOnRecalculation(object):
	if object.get(deleteOnRecalculation) is None:
		return False
	return True
	
	
def setStops(dataEmpty, stops):
	dataEmpty['stops'] = stops
	
	
def getLoadingTime(target):
	return target["loading time"]
def getStayTime(target):
	return target["stay time"]
def getWiggleScale(dataEmpty):
	return dataEmpty["wiggle scale"]
def getTravelValue():
	return round(getDataEmpty().get(travelPropertyName), 3)
	

def getCurrentSettingsHash():
	hash = getHashFromTargets()
	hash += str(getWiggleScale(getDataEmpty()))
	return hash
def getHashFromTargets():
	hash = ""
	targets = getTargetList()
	for target in targets:
		hash += getHashFromTarget(target)
	return hash
def getHashFromTarget(target):
	hash = str(getLoadingTime(target))
	hash += str(getStayTime(target))
	hash += str(target["easy in"])
	hash += str(target["easy out"])
	return hash


		
# interface
#############################

class TargetCameraPanel(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_category = "Animation"
	bl_label = "Target Camera"
	bl_context = "objectmode"
	
	@classmethod
	def poll(self, context):
		return targetCameraExists()
	
	def draw(self, context):		
		layout = self.layout
		
		camera = getTargetCamera()
		movement = getMovementEmpty()
		dataEmpty = getDataEmpty()
		targetList = getTargetList()
		
		layout.operator("camera_tools.recalculate_animation", text = "Recalculate")
			
		row = layout.row(align = True)
		row.operator("camera_tools.go_to_previous_target", icon = 'TRIA_LEFT', text = "")
		row.label("Travel: " + str(getTravelValue()))
		row.operator("camera_tools.go_to_next_target", icon = 'TRIA_RIGHT', text = "")
		
		box = layout.box()
		col = box.column(align = True)
		
		for i in range(len(targetList)):
			row = col.split(percentage=0.6, align = True)
			row.scale_y = 1.35
			name = row.operator("camera_tools.select_target", getTargetObjectFromTarget(targetList[i]).name)
			name.currentIndex = i
			up = row.operator("camera_tools.move_target_up", icon = 'TRIA_UP', text = "")
			up.currentIndex = i
			down = row.operator("camera_tools.move_target_down", icon = 'TRIA_DOWN', text = "")
			down.currentIndex = i
			delete = row.operator("camera_tools.delete_target", icon = 'X', text = "")
			delete.currentIndex = i
			if useListSeparator: col.separator()
		box.operator("camera_tools.new_target_object", icon = 'PLUS')
		
		selectedTargets = getSelectedTargets(targetList)
		for target in selectedTargets:
			box = layout.box()
			box.label(target.parent.name + "  (" + str(targetList.index(target) + 1) + ")")
			
			col = box.column(align = True)
			col.prop(target, '["loading time"]', slider = False, text = "Loading Time")
			col.prop(target, '["stay time"]', slider = False, text = "Time to Stay")
			
			col = box.column(align = True)
			col.prop(target, '["easy in"]', slider = False, text = "Slow In")
			col.prop(target, '["easy out"]', slider = False, text = "Slow Out")
			copyToAll = col.operator("camera_tools.copy_interpolation_properties_to_all", text = "Copy to All")
			copyToAll.currentIndex = targetList.index(target)			
			
		col = layout.column(align = True)
		col.label("Camera Wiggle")
		col.prop(dataEmpty, wiggleStrengthDataPath, text = "Strength")
		col.prop(dataEmpty, '["wiggle scale"]', text = "Time Scale")
		
		if getCurrentSettingsHash() != oldHash:
			layout.label("You should recalculate the animation", icon = 'ERROR')

		
		
	
# operators
#############################
		
class AddTargetCamera(bpy.types.Operator):
	bl_idname = "camera_tools.insert_target_camera"
	bl_label = "Add Target Camera"
	bl_description = "Create new active camera and create targets from selection."
	
	@classmethod
	def poll(self, context):
		return not targetCameraExists()
		
	def execute(self, context):
		insertTargetCamera()
		return{"FINISHED"}
		
class SetupTargetObject(bpy.types.Operator):
	bl_idname = "camera_tools.new_target_object"
	bl_label = "New Targets From Selection"
	bl_description = "Use selected objects as targets."
	
	def execute(self, context):
		newTargets()
		return{"FINISHED"}
		
class DeleteTargetOperator(bpy.types.Operator):
	bl_idname = "camera_tools.delete_target"
	bl_label = "Delete Target"
	bl_description = "Delete the target from the list."
	currentIndex = bpy.props.IntProperty()
	
	def execute(self, context):
		deleteTarget(self.currentIndex)
		return{"FINISHED"}
		
class RecalculateAnimationOperator(bpy.types.Operator):
	bl_idname = "camera_tools.recalculate_animation"
	bl_label = "Recalculate Animation"
	bl_description = "Regenerates most of the constraints, drivers and keyframes."
	
	def execute(self, context):
		createFullAnimation(getTargetList())
		return{"FINISHED"}
		
class MoveTargetUp(bpy.types.Operator):
	bl_idname = "camera_tools.move_target_up"
	bl_label = "Move Target Up"
	currentIndex = bpy.props.IntProperty()
	
	def execute(self, context):
		moveTargetUp(self.currentIndex)
		return{"FINISHED"}
		
class MoveTargetDown(bpy.types.Operator):
	bl_idname = "camera_tools.move_target_down"
	bl_label = "Move Target Down"
	currentIndex = bpy.props.IntProperty()
	
	def execute(self, context):
		moveTargetDown(self.currentIndex)
		return{"FINISHED"}		
		
class SelectTarget(bpy.types.Operator):
	bl_idname = "camera_tools.select_target"
	bl_label = "Select Target"
	bl_description = "Select that target."
	currentIndex = bpy.props.IntProperty()
	
	def execute(self, context):
		selectTarget(self.currentIndex)
		return{"FINISHED"}

class GoToNextTarget(bpy.types.Operator):		
	bl_idname = "camera_tools.go_to_next_target"
	bl_label = "Go To Next Target"
	bl_description = "Change frame to show next target."
	
	def execute(self, context):
		goToNextTarget()
		return{"FINISHED"}
		
class GoToPreviousTarget(bpy.types.Operator):		
	bl_idname = "camera_tools.go_to_previous_target"
	bl_label = "Go To Previous Target"
	bl_description = "Change frame to show previous target."
	
	def execute(self, context):
		goToPreviousTarget()
		return{"FINISHED"}
		
class CopyInterpolationPropertiesToAll(bpy.types.Operator):
	bl_idname = "camera_tools.copy_interpolation_properties_to_all"
	bl_label = "Copy Interpolation Properties"
	bl_description = "All targets will have these interpolation values."
	currentIndex = bpy.props.IntProperty()
	
	def execute(self, context):
		copyInterpolationProperties(self.currentIndex)
		return{"FINISHED"}

		
# register
#############################

def register():
	bpy.utils.register_module(__name__)

def unregister():
	bpy.utils.unregister_module(__name__)