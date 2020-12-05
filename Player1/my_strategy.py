from model import Action, EntityAction, BuildAction, MoveAction, AttackAction, RepairAction, AutoAttack
from model import DebugCommand, DebugData
from model import EntityType, Vec2Int
import time

# TODO build melee_base if none
# TODO workers up to 15, two houses at a time
# TODO implemetn NEED_HOUSE trigger and one more dedicated builder
# TODO stop searching by attack_range, not const 1
# TODO early def 19252
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
        self.attack_mode = False

    def get_action(self, player_view, debug_interface):
        self.times = []
        tstmp = time.time()

        entity_actions = {}
        game = Game(player_view.map_size, player_view.my_id, player_view.players)
        damap = Map(game.parse_entities(player_view.entities))

        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'Total res: {len(game.resources)}')))
        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'Obt res  : {len(game.obtainable_resources)}')))
        self.times.append(time.time()-tstmp)
        tstmp = time.time()

        # calcs for building repair
        try:
            house_to_repair1 = None
            house_to_repair2 = None
            rbarracks_to_repair = None
            need_house1 = False
            need_house2 = False
            house_not_in_progress1 = True
            house_not_in_progress2 = True
            rbarracks_not_in_progress = True

            if game.free_unit_slots < 3:
                need_house1 = True
            if game.free_unit_slots < 2:
                need_house2 = True
            for house in game.my_houses:
                if not house.active:
                    if house_to_repair1 is None:
                        house_to_repair1 = house
                        house_not_in_progress1 = False
                        break
                    elif house_to_repair2 is None:
                        house_to_repair2 = house
                        house_not_in_progress2 = False
                        break
            for rbarracks in game.my_ranged_bases:
                if not rbarracks.active:
                    rbarracks_to_repair = rbarracks
                    rbarracks_not_in_progress = False
                    break
            building_not_in_progress = house_not_in_progress1 and house_not_in_progress2 and rbarracks_not_in_progress
            need_house = need_house1 or need_house2

            dedicated_house_builders = 0
            dedicated_rbarracks_builder = 0
            if 14 < game.my_unit_count < 100:
                dedicated_house_builders = 2

            can_produce = True
            if need_house and building_not_in_progress:
                can_produce = False

        except:
            pass

        # bases
        try:
            # melee bases
            for my_melee_base in game.my_melee_bases:
                build_action = None
                if can_produce and game.my_resource_count >= 20 and len(game.my_ranged_units) > len(game.my_melee_units) + 20:
                    position = Vec2Int(my_melee_base.position.x+game.orientation[0], my_melee_base.position.y+game.orientation[1])
                    build_action = BuildAction(EntityType.MELEE_UNIT, position)
                entity_actions[my_melee_base.id] = EntityAction(None, build_action, None, None)

            # ranged bases
            for my_ranged_base in game.my_ranged_bases:
                build_action = None
                if can_produce and game.my_resource_count >= 30:
                    position = Vec2Int(my_ranged_base.position.x+game.orientation[0], my_ranged_base.position.y+game.orientation[1])
                    build_action = BuildAction(EntityType.RANGED_UNIT, position)
                entity_actions[my_ranged_base.id] = EntityAction(None, build_action, None, None)

            # main base
            for my_builder_base in game.my_builder_bases:
                build_action = None
                cond1 = can_produce and game.my_resource_count >= 10 and len(game.my_builder_units) <= 36 and (
                    len(game.my_builder_units) <= game.my_food_count // 2 + 2) and len(game.my_builder_units) <= len(game.resources) // 2
                cond2 = game.my_resource_count >= 10 and len(game.my_builder_units) < 16 and len(game.my_builder_units) <= len(game.resources) // 2
                if cond1 or cond2:
                    position = Vec2Int(my_builder_base.position.x+game.orientation[0], my_builder_base.position.y+game.orientation[1])
                    build_action = BuildAction(EntityType.BUILDER_UNIT, position)
                entity_actions[my_builder_base.id] = EntityAction(None, build_action, None, None)
        except:
            pass
        self.times.append(time.time()-tstmp)
        tstmp = time.time()

        # army
        try:
            if len(game.my_army) < 5 and len(game.my_ranged_bases) > 0 and len(game.my_builder_units) > 0:
                self.attack_mode = False
            elif len(game.my_army) > 8:
                self.attack_mode = True

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
        except:
            pass
        self.times.append(time.time()-tstmp)

        # turrets
        for turret in game.my_turrets:
            attack_action = AttackAction(None, AutoAttack(5, []))
            entity_actions[turret.id] = EntityAction(None, None, attack_action, None)

        tstmp = time.time()
        # building a rbarracks
        try:
            if (rbarracks_to_repair is not None) or (len(game.my_builder_units) > 20 and len(game.my_ranged_bases) == 1 and game.my_resource_count > 400):
                dedicated_rbarracks_builder = 1
                builder = game.my_builder_units[dedicated_house_builders]
                move_spot = None
                move_action = None
                build_action = None
                repair_action = None
                if rbarracks_to_repair is not None:
                    repair_action = RepairAction(rbarracks_to_repair.id)
                    move_spot = damap.find_move_spot(builder.position, rbarracks_to_repair.position, 5)
                    if move_spot is not None:
                        move_action = MoveAction(move_spot, True, False)
                    entity_actions[builder.id] = EntityAction(move_action, None, None, repair_action)
                else:
                    rbarracks_spot = damap.find_building_spot(6, builder.position)
                    if rbarracks_spot is not None:
                        build_action = BuildAction(EntityType.RANGED_BASE, rbarracks_spot)
                        move_spot = damap.find_move_spot(builder.position, rbarracks_spot, 5)
                        if move_spot is not None:
                            move_action = MoveAction(move_spot, True, False)
                        debug_interface.send(DebugCommand.Add(DebugData.Log(f'rbar     : {move_action}, {build_action}')))
                        entity_actions[builder.id] = EntityAction(move_action, build_action, None, None)
        except:
            pass

        # building a house
        try:
            # first
            if (house_to_repair1 is not None) or (game.free_unit_slots < 3 and len(game.my_builder_units)):
                dedicated_house_builders = max(dedicated_house_builders, 1)
                builder = game.my_builder_units[0]
                move_spot = None
                move_action = None
                build_action = None
                repair_action = None
                if house_to_repair1 is not None:
                    repair_action = RepairAction(house_to_repair1.id)
                    move_spot = damap.find_move_spot(builder.position, house_to_repair1.position, 3)
                    if move_spot is not None:
                        move_action = MoveAction(move_spot, True, False)
                    entity_actions[builder.id] = EntityAction(move_action, None, None, repair_action)
                else:
                    house_spot = damap.find_building_spot(3, builder.position)
                    if house_spot is not None:
                        build_action = BuildAction(EntityType.HOUSE, house_spot)
                        move_spot = damap.find_move_spot(builder.position, house_spot, 3)
                        if move_spot is not None:
                            move_action = MoveAction(move_spot, True, False)
                        entity_actions[builder.id] = EntityAction(move_action, build_action, None, None)

            # second
            if (house_to_repair2 is not None) or (game.free_unit_slots < 2 and len(game.my_builder_units)):
                dedicated_house_builders = max(dedicated_house_builders, 2)
                builder = game.my_builder_units[1]
                move_spot = None
                move_action = None
                build_action = None
                repair_action = None
                if house_to_repair2 is not None:
                    repair_action = RepairAction(house_to_repair2.id)
                    move_spot = damap.find_move_spot(builder.position, house_to_repair2.position, 3)
                    if move_spot is not None:
                        move_action = MoveAction(move_spot, True, False)
                    entity_actions[builder.id] = EntityAction(move_action, None, None, repair_action)
                else:
                    house_spot = damap.find_building_spot(3, builder.position)
                    if house_spot is not None:
                        build_action = BuildAction(EntityType.HOUSE, house_spot)
                        move_spot = damap.find_move_spot(builder.position, house_spot, 3)
                        if move_spot is not None:
                            move_action = MoveAction(move_spot, True, False)
                        entity_actions[builder.id] = EntityAction(move_action, build_action, None, None)
        except:
            pass
        self.times.append(time.time()-tstmp)
        tstmp = time.time()

        # gather resources
        try:
            for builder in game.my_builder_units[dedicated_house_builders+dedicated_rbarracks_builder:]:
                cur_pos = builder.position
                move_action = None
                attack_action = None
                dist, target_res, target_position = Calc.find_closest(cur_pos, game.obtainable_resources, game.map_size**2, game.res_avails)
                game.res_avails[target_res] = False
                move_action = MoveAction(target_position, True, False)
                attack_action = AttackAction(target_res, None)
                entity_actions[builder.id] = EntityAction(move_action, None, attack_action, None)
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
        debug_interface.get_state()
