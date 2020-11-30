import model

WALL = 0
HOUSE = 1
BUILDER_BASE = 2
BUILDER_UNIT = 3
MELEE_BASE = 4
MELEE_UNIT = 5
RANGED_BASE = 6
RANGED_UNIT = 7
RESOURCE = 8
TURRET = 9


class MyStrategy:

    def get_action(self, player_view, debug_interface):

        max_dist = player_view.map_size**2
        my_id = player_view.my_id
        my_resources = None
        enemies = []
        my_walls = []
        my_houses = []
        my_builder_bases = []
        my_builder_units = []
        my_melee_bases = []
        my_melee_units = []
        my_ranged_bases = []
        my_ranged_units = []
        resources = []
        res_avails = {}
        my_turrets = []
        enemy_units = []
        enemy_buildings = []
        entity_actions = {}

        for player in player_view.players:
            if player.id == my_id:
                my_resources = player.resource
            else:
                enemies.append(player.id)

        for entity in player_view.entities:
            if entity.entity_type == RESOURCE:
                resources.append(entity)
                res_avails[entity.id] = True
            if entity.player_id == my_id:
                if entity.entity_type == WALL:
                    my_walls.append(entity)
                elif entity.entity_type == HOUSE:
                    my_houses.append(entity)
                elif entity.entity_type == BUILDER_BASE:
                    my_builder_bases.append(entity)
                elif entity.entity_type == BUILDER_UNIT:
                    my_builder_units.append(entity)
                elif entity.entity_type == MELEE_BASE:
                    my_melee_bases.append(entity)
                elif entity.entity_type == MELEE_UNIT:
                    my_melee_units.append(entity)
                elif entity.entity_type == RANGED_BASE:
                    my_ranged_bases.append(entity)
                elif entity.entity_type == RANGED_UNIT:
                    my_ranged_units.append(entity)
                elif entity.entity_type == TURRET:
                    my_turrets.append(entity)
            else:
                if entity.entity_type in [MELEE_UNIT, RANGED_UNIT, TURRET, BUILDER_UNIT]:
                    enemy_units.append(entity)
                elif entity.entity_type in [WALL, HOUSE, BUILDER_BASE, MELEE_BASE, RANGED_BASE]:
                    enemy_buildings.append(entity)

        my_unit_count = len(my_builder_units) + \
            len(my_melee_units) + len(my_ranged_units)
        my_food_count = 15 + 5*len(my_houses)
        my_unit_slots = my_food_count - my_unit_count
        my_army = my_melee_units + my_ranged_units

        for artillery in my_ranged_bases:
            buildAction = None
            if my_unit_slots and my_resources > 29:
                position = model.Vec2Int(
                    artillery.position.x-1, artillery.position.y)
                buildAction = model.BuildAction(
                    model.EntityType.BUILDER_UNIT, position)
            entity_actions[artillery.id] = model.EntityAction(
                None, buildAction, None, None)

        for base in my_builder_bases:
            buildAction = None
            if my_unit_slots and my_resources > 9:
                position = model.Vec2Int(
                    base.position.x-1, base.position.y)
                buildAction = model.BuildAction(
                    model.EntityType.BUILDER_UNIT, position)
            entity_actions[base.id] = model.EntityAction(
                None, buildAction, None, None)

        for ship in my_army:
            cur_pos = ship.position
            moveAction = None
            attackAction = None
            dist = max_dist
            move_target = None
            attack_target = None
            if len(my_army) < 6:
                move_target = model.Vec2Int(
                    my_ranged_bases[0].position.x+4, my_ranged_bases[0].position.y+4)
            else:
                if len(enemy_units) > 0:
                    for unit in enemy_units:
                        cur_dist = (cur_pos.x - unit.position.x)**2 + \
                            (cur_pos.y - unit.position.y)**2
                        if cur_dist < dist:
                            dist = cur_dist
                            move_target = unit.position
                            attack_target = unit.id
                            if dist < 2:
                                break
                elif len(enemy_buildings) > 0:
                    for building in enemy_buildings:
                        cur_dist = (cur_pos.x - building.position.x)**2 + \
                            (cur_pos.y - building.position.y)**2
                        if cur_dist < dist:
                            dist = cur_dist
                            move_target = building.position
                            attack_target = building.id
                            if dist < 2:
                                break
            moveAction = model.MoveAction(move_target, True, False)
            attackAction = model.AttackAction(attack_target, None)
            entity_actions[ship.id] = model.EntityAction(
                moveAction, None, attackAction, None)

        for builder in my_builder_units:
            cur_pos = builder.position
            target_res = None
            moveAction = None
            attackAction = None
            dist = max_dist
            for res in resources:
                if res_avails[res.id]:
                    cur_dist = (cur_pos.x - res.position.x)**2 + \
                        (cur_pos.y - res.position.y)**2

                    if cur_dist < dist:
                        dist = cur_dist
                        target_res = res.id
                        target_position = res.position
                        if dist < 2:
                            break
            res_avails[target_res] = False
            moveAction = model.MoveAction(target_position, True, False)
            attackAction = model.AttackAction(target_res, None)
            entity_actions[builder.id] = model.EntityAction(
                moveAction, None, attackAction, None)

        # print("entity_actions: {}".format(entity_actions))
        return model.Action(entity_actions)

    def debug_update(self, player_view, debug_interface):
        debug_interface.send(model.DebugCommand.Clear())
        debug_interface.get_state()
