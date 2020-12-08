from model import Action, EntityAction, BuildAction, MoveAction, AttackAction, RepairAction, AutoAttack
from model import DebugCommand, DebugData
from model import EntityType, Vec2Int
import time

# TODO try sending troops in packs
# TODO better find_move_spot - closest
# TODO build turrets..
# TODO store state for gatherers (same as for building houses)
# TODO stop searching by attack_range, not const 1
# TODO break walls?
# TODO self.attack_mode rly needed?


class Calc:

    @staticmethod
    def distance_sqr(a, b):
        return (a.x - b.x) ** 2 + (a.y - b.y) ** 2

    @staticmethod
    def sign(a):
        result = None
        if a > 0:
            result = 1
        elif a < 0:
            result = -1
        else:
            result = 0
        return result

    @staticmethod
    def find_closest(cur_pos, targets, max_dist, available=None):
        dist = max_dist
        closest_target = None
        for target in targets:
            if available is not None:
                if not available[target.id]:
                    continue
            cur_dist = (cur_pos.x - target.position.x)**2 + (cur_pos.y - target.position.y)**2
            if cur_dist < dist:
                dist = cur_dist
                closest_target = target
                if dist < 2:
                    break
        return dist, closest_target.id, closest_target.position


class Map:
    def __init__(self, input):
        self.free_map = input[0]
        self.def_point = input[1]
        self.map_size = len(self.free_map)

    def find_move_spot(self, unit_pos, target_pos, target_size):
        # bottom
        available = True
        if target_pos.y-1 >= 0:
            try:
                for x in range(target_pos.x, target_pos.x+target_size):
                    if not self.free_map[x][target_pos.y-1]:
                        available = False
                        break
                    if available:
                        self.free_map[x][target_pos.y-1] = False
                        return Vec2Int(x, target_pos.y-1)
            except:
                pass
        # upper
        available = True
        try:
            for x in range(target_pos.x, target_pos.x+target_size):
                if not self.free_map[x][target_pos.y+target_size]:
                    available = False
                    break
                if available:
                    self.free_map[x][target_pos.y+target_size] = False
                    return Vec2Int(x, target_pos.y+target_size)
        except:
            pass
        # left
        if target_pos.x-1 >= 0:
            available = True
            try:
                for y in range(target_pos.y, target_pos.y+target_size):
                    if not self.free_map[target_pos.x-1][y]:
                        available = False
                        break
                    if available:
                        self.free_map[target_pos.x-1][y] = False
                        return Vec2Int(target_pos.x-1, y)
            except:
                pass
        # right
        available = True
        try:
            for y in range(target_pos.y, target_pos.y+target_size):
                if not self.free_map[target_pos.x+target_size][y]:
                    available = False
                    break
                if available:
                    self.free_map[target_pos.x+target_size][y] = False
                    return Vec2Int(target_pos.x+target_size, y)
        except:
            pass

        return None

    def find_building_spot(self, size, builder_position):
        start_x = 0
        start_y = 0
        increment_x = 1
        increment_y = 1
        free_map = self.free_map
        free_map[builder_position.x][builder_position.y] = True
        half = self.map_size // 2
        if self.def_point is not None:
            if self.def_point[0] > half:
                start_x = self.map_size - size
                increment_x = -1
            if self.def_point[0] > half:
                start_y = self.map_size - size
                increment_y = -1

        for z in range(0, self.map_size - size, size+1):
            for xy in range(0, z, size+1):
                x = start_x + increment_x * z
                y = start_y + increment_y * xy
                available = True
                for i in range(size):
                    for j in range(size):
                        available = self.free_map[x+i][y+j]
                        if not available:
                            break
                    if not available:
                        break
                if available:
                    for ii in range(x, x+size):
                        for jj in range(y, y+size):
                            self.free_map[ii][jj] = False
                    return Vec2Int(x, y)
                x = start_x + increment_x * xy
                y = start_y + increment_y * z
                available = True
                for i in range(size):
                    for j in range(size):
                        available = self.free_map[x+i][y+j]
                        if not available:
                            break
                    if not available:
                        break
                if available:
                    for ii in range(x, x+size):
                        for jj in range(y, y+size):
                            self.free_map[ii][jj] = False
                    return Vec2Int(x, y)
            x = start_x + increment_x * z
            y = start_y + increment_y * z
            available = True
            for i in range(size):
                for j in range(size):
                    available = self.free_map[x+i][y+j]
                    if not available:
                        break
                if not available:
                    break
            if available:
                for ii in range(x, x+size):
                    for jj in range(y, y+size):
                        self.free_map[ii][jj] = False
                return Vec2Int(x, y)
        return None


class Game:

    def __init__(self, map_size, my_id, players):

        self.map_size = map_size
        self.my_id = my_id
        self.enemy_ids = []
        self.my_resource_count = None
        for player in players:
            if player.id == my_id:
                self.my_resource_count = player.resource
            else:
                self.enemy_ids.append(player.id)
        self.my_walls = []
        self.my_houses = []
        self.my_builder_bases = []
        self.my_builder_units = []
        self.my_builder_units_ids = set()
        self.my_melee_bases = []
        self.my_melee_units = []
        self.my_ranged_bases = []
        self.my_ranged_units = []
        self.resources = []
        self.res_avails = {}
        self.my_turrets = []
        self.enemy_units = []
        self.enemy_buildings = []
        self.free_spots = [[True for _ in range(self.map_size)] for _ in range(self.map_size)]

    def parse_entities(self, entities):

        for entity in entities:
            if entity.entity_type == EntityType.RESOURCE:
                self.resources.append(entity)
                self.res_avails[entity.id] = True
                self.free_spots[entity.position.x][entity.position.y] = False
            if entity.player_id == self.my_id:
                if entity.entity_type == EntityType.WALL:
                    self.my_walls.append(entity)
                elif entity.entity_type == EntityType.HOUSE:
                    self.my_houses.append(entity)
                elif entity.entity_type == EntityType.BUILDER_BASE:
                    self.my_builder_bases.append(entity)
                elif entity.entity_type == EntityType.BUILDER_UNIT:
                    self.my_builder_units.append(entity)
                    self.my_builder_units_ids.add(entity.id)
                elif entity.entity_type == EntityType.MELEE_BASE:
                    self.my_melee_bases.append(entity)
                elif entity.entity_type == EntityType.MELEE_UNIT:
                    self.my_melee_units.append(entity)
                elif entity.entity_type == EntityType.RANGED_BASE:
                    self.my_ranged_bases.append(entity)
                elif entity.entity_type == EntityType.RANGED_UNIT:
                    self.my_ranged_units.append(entity)
                elif entity.entity_type == EntityType.TURRET:
                    self.my_turrets.append(entity)
            else:
                if entity.entity_type in {EntityType.TURRET, EntityType.BUILDER_UNIT, EntityType.MELEE_UNIT, EntityType.RANGED_UNIT}:
                    self.enemy_units.append(entity)
                elif entity.entity_type in {EntityType.WALL, EntityType.HOUSE, EntityType.BUILDER_BASE, EntityType.MELEE_BASE, EntityType.RANGED_BASE}:
                    self.enemy_buildings.append(entity)

            if entity.entity_type in {EntityType.WALL, EntityType.BUILDER_UNIT, EntityType.MELEE_UNIT, EntityType.RANGED_UNIT}:
                self.free_spots[entity.position.x][entity.position.y] = False
            elif entity.entity_type == EntityType.TURRET:
                for i in range(2):
                    for j in range(2):
                        self.free_spots[entity.position.x+i][entity.position.y+j] = False
            elif entity.entity_type == EntityType.HOUSE:
                for i in range(3):
                    for j in range(3):
                        self.free_spots[entity.position.x+i][entity.position.y+j] = False
            elif entity.entity_type in {EntityType.BUILDER_BASE, EntityType.MELEE_BASE, EntityType.RANGED_BASE}:
                for i in range(5):
                    for j in range(5):
                        self.free_spots[entity.position.x+i][entity.position.y+j] = False

        self.my_builder_units.sort(key=lambda entity: entity.id)
        self.my_houses.sort(key=lambda entity: entity.id)

        self.obtainable_resources = []
        res_coords = set()
        for res in self.resources:
            res_coords.add((res.position.x, res.position.y))
        for res in self.resources:
            coord = (res.position.x, res.position.y)
            addable = False
            if (coord[0]-1 >= 0) and (coord[0]-1, coord[1]) not in res_coords:
                addable = True
            elif (coord[0]+1 < self.map_size) and (coord[0]+1, coord[1]) not in res_coords:
                addable = True
            elif (coord[1]-1 >= 0) and (coord[0], coord[1]-1) not in res_coords:
                addable = True
            elif (coord[1]+1 < self.map_size) and (coord[0], coord[1]+1) not in res_coords:
                addable = True
            if addable:
                self.obtainable_resources.append(res)

        self.my_unit_count = len(self.my_builder_units) + len(self.my_melee_units) + len(self.my_ranged_units)
        self.my_food_prod = self.my_builder_bases + self.my_melee_bases + self.my_ranged_bases + self.my_houses
        self.my_food_prod = [entity for entity in self.my_food_prod if entity.active]
        self.my_food_count = 5*len(self.my_food_prod)
        self.free_unit_slots = self.my_food_count - self.my_unit_count
        self.my_army = self.my_melee_units + self.my_ranged_units

        self.my_prod = self.my_builder_bases + self.my_melee_bases + self.my_ranged_bases

        self.orientation = (-1, 0)
        self.def_point = None
        half = self.map_size // 2
        if len(self.my_prod):
            position = self.my_prod[0].position
            if position.x > half:
                if position.y > half:
                    self.orientation = (-1, 0)
                    self.def_point = (self.map_size-12, self.map_size-12)
                else:
                    self.orientation = (-1, 4)
                    self.def_point = (self.map_size-12, 12)
            elif position.y > half:
                self.orientation = (5, 0)
                self.def_point = (12, self.map_size-12)
            else:
                self.orientation = (5, 4)
                self.def_point = (12, 12)

        try:
            self.obtainable_resources.sort(key=lambda res: (res.position.x-self.def_point[0])**2 + (res.position.y-self.def_point[1])**2)
        except:
            pass

        for entity in self.my_prod:
            self.free_spots[entity.position.x+self.orientation[0]][entity.position.y+self.orientation[1]] = False

        return self.free_spots, self.def_point


class MyStrategy:

    def __init__(self):
        self.times = []
        self.commands_this_turn = []
        self.attack_mode = False
        self.need_houses = 0
        self.houses_in_progress = []
        self.dedicated_house_builders = []
        self.can_produce = None
        self.buider_tasks = [[None, None, None], [None, None, None], [None, None, None]]

    def precalc(self, game):
        rbarracks_to_repair = None
        mbarracks_to_repair = None
        self.need_houses = 0
        self.can_produce = True
        unrepaired_houses = []
        for house in game.my_houses:
            if not house.active:
                unrepaired_houses.append(house)
        unrepaired_houses_ids = []
        for house in unrepaired_houses:
            unrepaired_houses_ids.append(house.id)
        self.houses_in_progress = [house for house in self.houses_in_progress if house.id in unrepaired_houses_ids]
        for house in unrepaired_houses:
            if house not in self.houses_in_progress:
                self.houses_in_progress.append(house)
        houses_in_progress_ids = []
        for house in self.houses_in_progress:
            houses_in_progress_ids.append(house.id)
        for task in self.buider_tasks:
            if (task[2] is not None) and (task[2].id not in houses_in_progress_ids):
                task[2] = None
        if game.my_food_count > 20 and game.my_unit_count < 16:
            self.need_houses = 0
        elif game.my_unit_count > 14 and game.free_unit_slots < 3 and len(self.houses_in_progress) < 2:
            self.need_houses = 2 - len(self.houses_in_progress)
        need_dedicated_house_builders = 0
        self.dedicated_house_builders = [builder for builder in self.dedicated_house_builders if builder.id in game.my_builder_units_ids]
        if game.my_unit_count > 14:
            need_dedicated_house_builders = 3
            if game.my_food_count > 100:
                need_dedicated_house_builders = 2
        if len(self.dedicated_house_builders) != need_dedicated_house_builders:
            self.dedicated_house_builders = []
            for i in range(need_dedicated_house_builders):
                entity = game.my_builder_units.pop(0)
                self.dedicated_house_builders.append(entity)
                self.buider_tasks[i][0] = entity
                self.buider_tasks[i][1] = None
                self.buider_tasks[i][2] = None
        else:
            for i in range(need_dedicated_house_builders):
                game.my_builder_units.pop(0)
        for rbarracks in game.my_ranged_bases:
            if not rbarracks.active:
                rbarracks_to_repair = rbarracks
                break
        for mbarracks in game.my_melee_bases:
            if not mbarracks.active:
                mbarracks_to_repair = mbarracks
                break
        if self.need_houses:
            self.can_produce = False
        if len(game.my_army) < 5 and (len(game.my_ranged_bases) > 0 or len(game.my_melee_bases) > 0) and len(game.my_builder_units) > 0:
            self.attack_mode = False
        elif len(game.my_army) > 8:
            self.attack_mode = True

        return mbarracks_to_repair, rbarracks_to_repair

    def command_prod(self, game, entity_actions):
        # melee bases
        for my_melee_base in game.my_melee_bases:
            build_action = None
            if self.can_produce and game.my_resource_count >= 20 and ((len(game.my_ranged_units) > len(game.my_melee_units) + 6) or len(game.my_ranged_bases) == 0):
                position = Vec2Int(my_melee_base.position.x+game.orientation[0], my_melee_base.position.y+game.orientation[1])
                build_action = BuildAction(EntityType.MELEE_UNIT, position)
            entity_actions[my_melee_base.id] = EntityAction(None, build_action, None, None)

        # ranged bases
        for my_ranged_base in game.my_ranged_bases:
            build_action = None
            if self.can_produce and game.my_resource_count >= 30:
                position = Vec2Int(my_ranged_base.position.x+game.orientation[0], my_ranged_base.position.y+game.orientation[1])
                build_action = BuildAction(EntityType.RANGED_UNIT, position)
            entity_actions[my_ranged_base.id] = EntityAction(None, build_action, None, None)

        # main base
        for my_builder_base in game.my_builder_bases:
            build_action = None
            cond1 = self.can_produce and game.my_resource_count >= 10 and len(game.my_builder_units) <= 36 and (
                len(game.my_builder_units) <= game.my_food_count // 2 + 2) and len(game.my_builder_units) <= len(game.resources) // 2
            cond2 = game.my_resource_count >= 10 and len(game.my_builder_units) < 16 and len(game.my_builder_units) <= len(game.resources) // 2
            if cond1 or cond2:
                position = Vec2Int(my_builder_base.position.x+game.orientation[0], my_builder_base.position.y+game.orientation[1])
                build_action = BuildAction(EntityType.BUILDER_UNIT, position)
            entity_actions[my_builder_base.id] = EntityAction(None, build_action, None, None)

    def command_army(self, game, entity_actions):
        for battle_ship in game.my_army:
            cur_pos = battle_ship.position
            move_action = None
            attack_action = None
            move_target = None
            attack_target = None

            if not self.attack_mode:
                move_target = Vec2Int(game.def_point[0], game.def_point[1])
            else:
                if len(game.enemy_units) > 0:
                    dist, attack_target, move_target = Calc.find_closest(cur_pos, game.enemy_units, game.map_size**2)
                elif len(game.enemy_buildings) > 0:
                    dist, attack_target, move_target = Calc.find_closest(cur_pos, game.enemy_buildings, game.map_size**2)
            if move_target is not None:
                move_action = MoveAction(move_target, True, True)
                attack_action = AttackAction(attack_target, AutoAttack(20, []))
            entity_actions[battle_ship.id] = EntityAction(move_action, None, attack_action, None)

        for turret in game.my_turrets:
            attack_action = AttackAction(None, AutoAttack(5, []))
            entity_actions[turret.id] = EntityAction(None, None, attack_action, None)

    def command_build_prod(self, game, damap, entity_actions, mbarracks_to_repair, rbarracks_to_repair):
        if (rbarracks_to_repair is not None) or (len(game.my_builder_units) > 20 and len(game.my_ranged_bases) < 1 and game.my_resource_count > 440):
            builder = game.my_builder_units.pop(0)
            move_spot = None
            move_action = None
            build_action = None
            repair_action = None
            if rbarracks_to_repair is not None:
                builder2 = game.my_builder_units.pop(0)
                repair_action = RepairAction(rbarracks_to_repair.id)
                move_spot = damap.find_move_spot(builder.position, rbarracks_to_repair.position, 5)
                move_spot2 = damap.find_move_spot(builder2.position, rbarracks_to_repair.position, 5)
                if move_spot is not None:
                    move_action = MoveAction(move_spot, True, False)
                if move_spot2 is not None:
                    move_action2 = MoveAction(move_spot2, True, False)
                entity_actions[builder.id] = EntityAction(move_action, None, None, repair_action)
                entity_actions[builder2.id] = EntityAction(move_action2, None, None, repair_action)
            else:
                rbarracks_spot = damap.find_building_spot(6, builder.position)
                if rbarracks_spot is not None:
                    build_action = BuildAction(EntityType.RANGED_BASE, rbarracks_spot)
                    move_spot = damap.find_move_spot(builder.position, rbarracks_spot, 5)
                    if move_spot is not None:
                        move_action = MoveAction(move_spot, True, False)
                    entity_actions[builder.id] = EntityAction(move_action, build_action, None, None)

        elif (mbarracks_to_repair is not None) or (len(game.my_builder_units) > 20 and len(game.my_melee_bases) < 1 and game.my_resource_count > 440):
            builder = game.my_builder_units.pop(0)
            move_spot = None
            move_action = None
            build_action = None
            repair_action = None
            if mbarracks_to_repair is not None:
                builder2 = game.my_builder_units.pop(0)
                repair_action = RepairAction(mbarracks_to_repair.id)
                move_spot = damap.find_move_spot(builder.position, mbarracks_to_repair.position, 5)
                move_spot2 = damap.find_move_spot(builder2.position, mbarracks_to_repair.position, 5)
                if move_spot is not None:
                    move_action = MoveAction(move_spot, True, False)
                if move_spot2 is not None:
                    move_action2 = MoveAction(move_spot2, True, False)
                entity_actions[builder.id] = EntityAction(move_action, None, None, repair_action)
                entity_actions[builder2.id] = EntityAction(move_action2, None, None, repair_action)
            else:
                mbarracks_spot = damap.find_building_spot(6, builder.position)
                if mbarracks_spot is not None:
                    build_action = BuildAction(EntityType.MELEE_BASE, mbarracks_spot)
                    move_spot = damap.find_move_spot(builder.position, mbarracks_spot, 5)
                    if move_spot is not None:
                        move_action = MoveAction(move_spot, True, False)
                    entity_actions[builder.id] = EntityAction(move_action, build_action, None, None)

    def command_build_houses(self, game, damap, entity_actions):
        # repair
        for house_to_repair in self.houses_in_progress:
            for task in self.buider_tasks:
                if house_to_repair not in {self.buider_tasks[0][2], self.buider_tasks[1][2]}:
                    if task[1] is not None:
                        if (task[1].position.x == house_to_repair.position.x) and (task[1].position.y == house_to_repair.position.y):
                            task[1] = None
                    if task[1] is None and task[2] is None:
                        move_action = None
                        build_action = None
                        repair_action = RepairAction(house_to_repair.id)
                        task[2] = house_to_repair
                        move_spot = damap.find_move_spot(task[0].position, house_to_repair.position, 3)
                        if move_spot is not None:
                            move_action = MoveAction(move_spot, True, False)
                        entity_action = EntityAction(move_action, None, None, repair_action)
                        entity_actions[task[0].id] = entity_action
                        self.commands_this_turn.append(entity_action)
        # build
        if self.need_houses:
            for task in self.buider_tasks[:2]:
                if task[1] is None and task[2] is None:
                    move_spot = None
                    move_action = None
                    build_action = None
                    repair_action = None
                    house_spot = damap.find_building_spot(3, task[0].position)
                    if house_spot is not None:
                        build_action = BuildAction(EntityType.HOUSE, house_spot)
                        move_spot = damap.find_move_spot(task[0].position, house_spot, 3)
                        if move_spot is not None:
                            move_action = MoveAction(move_spot, True, False)
                        task[1] = build_action
                        entity_action = EntityAction(move_action, build_action, None, None)
                        entity_actions[task[0].id] = entity_action
                        self.commands_this_turn.append(entity_action)

    def command_miners(self, game, entity_actions):
        for builder in game.my_builder_units:
            cur_pos = builder.position
            move_action = None
            attack_action = None
            dist, target_res, target_position = Calc.find_closest(cur_pos, game.obtainable_resources, game.map_size**2, game.res_avails)
            game.res_avails[target_res] = False
            move_action = MoveAction(target_position, True, False)
            attack_action = AttackAction(target_res, None)
            entity_actions[builder.id] = EntityAction(move_action, None, attack_action, None)

    def get_action(self, player_view, debug_interface):
        self.times = []
        self.commands_this_turn = []
        tstmp = time.time()

        entity_actions = {}
        game = Game(player_view.map_size, player_view.my_id, player_view.players)
        damap = Map(game.parse_entities(player_view.entities))

        self.times.append(time.time()-tstmp)
        tstmp = time.time()

        try:
            mbarracks_to_repair, rbarracks_to_repair = self.precalc(game)
        except:
            mbarracks_to_repair, rbarracks_to_repair = 0, 0

        try:
            self.command_prod(game, entity_actions)
        except:
            pass

        self.times.append(time.time()-tstmp)
        tstmp = time.time()

        try:
            self.command_army(game, entity_actions)
        except:
            pass

        self.times.append(time.time()-tstmp)
        tstmp = time.time()

        try:
            self.command_build_prod(game, damap, entity_actions, mbarracks_to_repair, rbarracks_to_repair)
        except:
            pass

        try:
            self.command_build_houses(game, damap, entity_actions)
        except:
            pass

        self.times.append(time.time()-tstmp)
        tstmp = time.time()

        try:
            self.command_miners(game, entity_actions)
        except:
            pass

        self.times.append(time.time()-tstmp)

        return Action(entity_actions)

    def debug_update(self, player_view, debug_interface):
        debug_interface.send(DebugCommand.Clear())
        if len(self.times) > 0:
            debug_interface.send(DebugCommand.Add(DebugData.Log(f'Init     : {self.times[0]*1000:.2f}')))
            debug_interface.send(DebugCommand.Add(DebugData.Log(f'Bases    : {self.times[1]*1000:.2f}')))
            debug_interface.send(DebugCommand.Add(DebugData.Log(f'Army     : {self.times[2]*1000:.2f}')))
            debug_interface.send(DebugCommand.Add(DebugData.Log(f'Constract: {self.times[3]*1000:.2f}')))
            debug_interface.send(DebugCommand.Add(DebugData.Log(f'Resourses: {self.times[4]*1000:.2f}')))
        # if len(self.workers) > 0:
        #     debug_interface.send(DebugCommand.Add(DebugData.Log(f'Workers: {self.workers}')))
        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'can_produce: {self.can_produce}')))
        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'need_houses: {self.need_houses}')))
        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'houses_in_progress: {self.houses_in_progress}')))
        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'buider_tasks: {self.buider_tasks}')))
        for command in self.commands_this_turn:
            debug_interface.send(DebugCommand.Add(DebugData.Log(f'command: {command}')))
        debug_interface.get_state()
