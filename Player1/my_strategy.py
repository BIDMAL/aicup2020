from model import Action, EntityAction, BuildAction, MoveAction, AttackAction, RepairAction, AutoAttack
from model import DebugCommand, DebugData
from model import EntityType, Vec2Int
import numpy as np
import time

# TODO:
# TIME FAIL
# heatup ignores size
# build in Round2
# ranged kite melee, don't build melee
# army doesn't suicide 1 by 1
# probes repair turrets when enemy army's nearby
# try sending troops in packs
# build turrets


class Calc:

    @staticmethod
    def heatup_map(position, hmap, radius, offset=0, size=1):

        posx = position.x + offset
        posy = position.y + offset
        for x in range(0, radius+1):
            hmap[posx+x, posy-radius+x] += 1
            hmap[posx-x, posy+radius-x+1] += 1

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

        dist = max_dist**2
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

    @staticmethod
    def find_closest_pos(cur_pos, targets, max_dist):

        dist = max_dist**2
        closest_target = None
        for target in targets:
            cur_dist = (cur_pos.x - target[0])**2 + (cur_pos.y - target[1])**2
            if cur_dist < dist:
                dist = cur_dist
                closest_target = target
                if dist < 2:
                    break
        return dist, closest_target[0], closest_target[1]


class Worker:

    def __init__(self, wid, pos):

        self.id = wid
        self.pos = pos
        self.mov = None
        self.res = None
        self.rep = None


class Map:

    def __init__(self, params):

        self.map_size = params[0]
        self.my_id = params[1]
        self.hmap_miners = np.array(np.zeros((self.map_size+20, self.map_size+20)), dtype='i4')
        self.hmap_enemies = np.array(np.zeros((self.map_size+20, self.map_size+20)), dtype='i4')
        self.free_map = np.array(np.ones((self.map_size, self.map_size)), dtype=bool)
        self.orientation = (-1, 0)
        self.def_point = (17, 17)
        self.res_ids = set()
        self.res_coords = set()
        self.obtainable_resources = []
        self.resources = params[2]
        entities = params[3]

        for entity in entities:
            if entity.player_id == self.my_id:
                if entity.entity_type == EntityType.BUILDER_UNIT:
                    # Calc.heatup_map(entity.position, self.hmap_miners, 8, offset=10)
                    pass
                elif entity.entity_type in {EntityType.BUILDER_BASE, EntityType.MELEE_BASE, EntityType.RANGED_BASE}:
                    self.free_map[entity.position.x+5, entity.position.y+4] = False
            else:
                if entity.entity_type == EntityType.TURRET:
                    pass
                    # Calc.heatup_map(entity.position, self.hmap_enemies, 8, offset=10, size=2)
                elif entity.entity_type == EntityType.MELEE_UNIT:
                    Calc.heatup_map(entity.position, self.hmap_enemies, 2, offset=10)
                elif entity.entity_type == EntityType.RANGED_UNIT:
                    Calc.heatup_map(entity.position, self.hmap_enemies, 6, offset=10)
            if entity.entity_type == EntityType.RESOURCE:
                self.res_coords.add((entity.position.x, entity.position.y))
                self.res_ids.add(entity.id)
                self.free_map[entity.position.x, entity.position.y] = False
            if entity.entity_type in {EntityType.WALL, EntityType.BUILDER_UNIT, EntityType.MELEE_UNIT, EntityType.RANGED_UNIT}:
                self.free_map[entity.position.x, entity.position.y] = False
            elif entity.entity_type == EntityType.TURRET:
                for i in range(2):
                    for j in range(2):
                        self.free_map[entity.position.x+i, entity.position.y+j] = False
            elif entity.entity_type == EntityType.HOUSE:
                for i in range(3):
                    for j in range(3):
                        self.free_map[entity.position.x+i, entity.position.y+j] = False
            elif entity.entity_type in {EntityType.BUILDER_BASE, EntityType.MELEE_BASE, EntityType.RANGED_BASE}:
                for i in range(5):
                    for j in range(5):
                        self.free_map[entity.position.x+i, entity.position.y+j] = False

        self.hmap_miners = np.array(self.hmap_miners[10:self.map_size+10, 10:self.map_size+10])
        self.hmap_enemies = np.array(self.hmap_enemies[10:self.map_size+10, 10:self.map_size+10])

    def find_move_spot(self, unit_pos, target_pos, target_size):

        # bottom
        available_spots = []
        if target_pos.y-1 >= 0:
            try:
                for x in range(target_pos.x, target_pos.x+target_size):
                    if self.free_map[x, target_pos.y-1]:
                        available_spots.append((x, target_pos.y-1))
            except:
                pass
        # upper
        if target_pos.y+target_size < self.map_size:
            try:
                for x in range(target_pos.x, target_pos.x+target_size):
                    if self.free_map[x][target_pos.y+target_size]:
                        available_spots.append((x, target_pos.y+target_size))
            except:
                pass
        # left
        if target_pos.x-1 >= 0:
            try:
                for y in range(target_pos.y, target_pos.y+target_size):
                    if self.free_map[target_pos.x-1, y]:
                        available_spots.append((target_pos.x-1, y))
            except:
                pass
        # right
        if target_pos.x+target_size < self.map_size:
            try:
                for y in range(target_pos.y, target_pos.y+target_size):
                    if self.free_map[target_pos.x+target_size, y]:
                        available_spots.append((target_pos.x+target_size, y))
            except:
                pass

        target_pos = None
        if len(available_spots):
            dist, x, y = Calc.find_closest_pos(unit_pos, available_spots, self.map_size)
            target_pos = Vec2Int(x, y)
            self.free_map[x, y] = False

        return target_pos

    def find_building_spot(self, size, builder_position, builder_num=1):

        start_x = 0
        start_y = 0
        free_map = self.free_map
        free_map[builder_position.x, builder_position.y] = True

        for z in range(0, self.map_size - size, size+2):
            for xy in range(0, z, size+2):
                x = start_x + z
                y = start_y + xy
                available = True
                for i in range(size):
                    for j in range(size):
                        available = self.free_map[x+i, y+j]
                        if not available:
                            break
                    if not available:
                        break
                if available:
                    for ii in range(x, x+size):
                        for jj in range(y, y+size):
                            self.free_map[ii, jj] = False
                    free_map[builder_position.x, builder_position.y] = False
                    return Vec2Int(x, y)
                x = start_x + xy
                y = start_y + z
                available = True
                for i in range(size):
                    for j in range(size):
                        available = self.free_map[x+i, y+j]
                        if not available:
                            break
                    if not available:
                        break
                if available:
                    for ii in range(x, x+size):
                        for jj in range(y, y+size):
                            self.free_map[ii, jj] = False
                    free_map[builder_position.x, builder_position.y] = False
                    return Vec2Int(x, y)
            x = start_x + z
            y = start_y + z
            available = True
            for i in range(size):
                for j in range(size):
                    available = self.free_map[x+i, y+j]
                    if not available:
                        break
                if not available:
                    break
            if available:
                for ii in range(x, x+size):
                    for jj in range(y, y+size):
                        self.free_map[ii, jj] = False
                free_map[builder_position.x, builder_position.y] = False
                return Vec2Int(x, y)

        return None

    def calc_obtainable_resources(self):

        self.obtainable_resources = []
        for res in self.resources:
            coord = (res.position.x, res.position.y)
            addable = False
            if self.hmap_enemies[coord[0], coord[1]]:
                continue
            if (coord[0]-1 >= 0) and ((coord[0]-1, coord[1]) not in self.res_coords) and self.free_map[coord[0]-1, coord[1]]:
                addable = True
            elif (coord[0]+1 < self.map_size) and (coord[0]+1, coord[1]) not in self.res_coords and self.free_map[coord[0]+1, coord[1]]:
                addable = True
            elif (coord[1]-1 >= 0) and (coord[0], coord[1]-1) not in self.res_coords and self.free_map[coord[0], coord[1]-1]:
                addable = True
            elif (coord[1]+1 < self.map_size) and (coord[0], coord[1]+1) not in self.res_coords and self.free_map[coord[0], coord[1]+1]:
                addable = True
            if addable:
                self.obtainable_resources.append(res)

        try:
            self.obtainable_resources.sort(key=lambda res: (res.position.x)**2 + (res.position.y)**2)
        except:
            pass


class Game:

    def __init__(self, my_id, players, tick):

        self.my_id = my_id
        self.enemy_ids = []
        self.my_resource_count = None
        for player in players:
            if player.id == my_id:
                self.my_resource_count = player.resource
            else:
                self.enemy_ids.append(player.id)
        self.tick = tick
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

    def parse_entities(self, entities, map_size):

        for entity in entities:
            if entity.entity_type == EntityType.RESOURCE:
                self.resources.append(entity)
                self.res_avails[entity.id] = True
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

        self.my_builder_units.sort(key=lambda entity: entity.id)
        self.my_houses.sort(key=lambda entity: entity.id)

        self.my_unit_count = len(self.my_builder_units) + len(self.my_melee_units) + len(self.my_ranged_units)
        self.my_food_prod = self.my_builder_bases + self.my_melee_bases + self.my_ranged_bases + self.my_houses
        self.my_food_prod = [entity for entity in self.my_food_prod if entity.active]
        self.my_food_count = 5*len(self.my_food_prod)
        self.free_unit_slots = self.my_food_count - self.my_unit_count
        self.my_army = self.my_melee_units + self.my_ranged_units
        self.my_prod = self.my_melee_bases + self.my_ranged_bases

        return map_size, self.my_id, self.resources, entities


class MyStrategy:

    def __init__(self):
        self.times = 0
        self.attack_mode = False
        self.need_houses = 0
        self.houses_in_progress = []
        self.dedicated_house_builders = []
        self.can_produce = None
        self.house_buider_tasks = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.need_prod = 0
        self.prod_in_progress = []
        self.dedicated_prod_builders = []
        self.prod_buider_tasks = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
        self.my_miners = dict()

    def precalc(self, game, damap, entity_actions):

        self.need_houses = 0
        self.need_prod = 0
        self.can_produce = True

        # spot move_spots
        for task in self.house_buider_tasks:
            if task[3] is not None:
                damap.free_map[task[3].x, task[3].y] = False
        for task in self.house_buider_tasks:
            if task[3] is not None:
                damap.free_map[task[3].x, task[3].y] = False

        # houses
        unrepaired_houses = []
        for house in game.my_houses:
            if not house.active:
                unrepaired_houses.append(house)
        unrepaired_houses_ids = []
        for house in unrepaired_houses:
            unrepaired_houses_ids.append(house.id)
        self.houses_in_progress = [house for house in self.houses_in_progress if house.id in unrepaired_houses_ids]
        houses_in_progress_ids = [house.id for house in self.houses_in_progress]
        for house in unrepaired_houses:
            if house.id not in houses_in_progress_ids:
                houses_in_progress_ids.append(house.id)
                self.houses_in_progress.append(house)
        for task in self.house_buider_tasks:
            if (task[2] is not None) and (task[2].id not in houses_in_progress_ids):
                task[1] = None
                task[2] = None
                task[3] = None
                entity_actions[task[0].id] = EntityAction(None, None, None, None)
            if task[1] is not None:
                damap.free_map[task[1].position.x, task[1].position.y] = False

        if game.my_food_count > 20 and game.my_unit_count < 16:
            self.need_houses = 0
        elif game.my_unit_count > 13 and game.free_unit_slots < 6 and len(self.houses_in_progress) < 2:
            self.need_houses = 2 - len(self.houses_in_progress)
        need_dedicated_house_builders = 0
        self.dedicated_house_builders = [builder for builder in self.dedicated_house_builders if builder.id in game.my_builder_units_ids]
        if game.my_unit_count > 13:
            need_dedicated_house_builders = 4
            if game.my_food_count > 100:
                need_dedicated_house_builders = 2
        if len(self.dedicated_house_builders) != need_dedicated_house_builders:
            self.dedicated_house_builders = []
            for i in range(need_dedicated_house_builders):
                entity = game.my_builder_units.pop(0)
                self.dedicated_house_builders.append(entity)
                self.house_buider_tasks[i][0] = entity
                self.house_buider_tasks[i][1] = None
                self.house_buider_tasks[i][2] = None
                self.house_buider_tasks[i][3] = None
                entity_actions[entity.id] = EntityAction(MoveAction(Vec2Int(5, 5), True, False), None, None, None)
        else:
            for i in range(need_dedicated_house_builders):
                game.my_builder_units.pop(0)

        # prod
        unrepaired_prod = []

        for prod in game.my_prod:
            if not prod.active:
                unrepaired_prod.append(prod)
        unrepaired_prod_ids = []
        for prod in unrepaired_prod:
            unrepaired_prod_ids.append(prod.id)
        self.prod_in_progress = [prod for prod in self.prod_in_progress if prod.id in unrepaired_prod_ids]
        for prod in unrepaired_prod:
            if prod not in self.prod_in_progress:
                self.prod_in_progress.append(prod)
        prods_in_progress_ids = []
        for prod in self.prod_in_progress:
            prods_in_progress_ids.append(prod.id)
        for task in self.prod_buider_tasks:
            if (task[2] is not None) and (task[2].id not in prods_in_progress_ids):
                task[1] = None
                task[2] = None
                task[3] = None
            if task[1] is not None:
                damap.free_map[task[1].position.x, task[1].position.y] = False

        if (game.my_resource_count > 400) and (len(game.my_ranged_bases) < 1 or len(game.my_melee_bases) < 1):
            self.need_prod = 1
        need_dedicated_prod_builders = 0
        self.dedicated_prod_builders = [builder for builder in self.dedicated_prod_builders if builder.id in game.my_builder_units_ids]
        if self.need_prod:
            need_dedicated_prod_builders = 2
        if len(self.dedicated_prod_builders) != need_dedicated_prod_builders:
            self.dedicated_prod_builders = []
            for i in range(need_dedicated_prod_builders):
                entity = game.my_builder_units.pop(0)
                self.dedicated_prod_builders.append(entity)
                self.prod_buider_tasks[i][0] = entity
                self.prod_buider_tasks[i][1] = None
                self.prod_buider_tasks[i][2] = None
                self.prod_buider_tasks[i][3] = None
        else:
            for i in range(need_dedicated_prod_builders):
                game.my_builder_units.pop(0)

        # miners
        alive_miners_ids = set()
        prev_miners_ids = set(self.my_miners.keys())
        for miner in game.my_builder_units:
            alive_miners_ids.add(miner.id)
            if miner.id not in prev_miners_ids:
                self.my_miners[miner.id] = Worker(miner.id, miner.position)
            else:
                self.my_miners[miner.id].pos = miner.position
        for prev_miners_id in prev_miners_ids:
            if prev_miners_id not in alive_miners_ids:
                del(self.my_miners[prev_miners_id])
        for key, val in self.my_miners.items():
            if val.res is not None:
                if val.res not in damap.res_ids:
                    self.my_miners[key].res = None
                else:
                    game.res_avails[val.res] = False

        # can_produce, attack_mode
        cond1 = self.need_houses and (game.my_resource_count < self.need_houses*(50 + len(game.my_houses)))
        cond2 = self.need_prod and game.my_resource_count < 500
        if cond1 or cond2:
            self.can_produce = False
        if len(game.my_army) < (5 + len(game.my_houses)) and (len(game.my_ranged_bases) > 0 or len(game.my_melee_bases) > 0) and len(game.my_builder_units) > 0:
            self.attack_mode = False
        elif len(game.my_army) > (10 + len(game.my_houses)):
            self.attack_mode = True

    def command_prod(self, game, entity_actions):

        # melee bases
        for my_melee_base in game.my_melee_bases:
            build_action = None
            if self.can_produce and game.my_resource_count >= 20 and ((len(game.my_ranged_units) > len(game.my_melee_units) + 6) or len(game.my_ranged_bases) == 0):
                position = Vec2Int(my_melee_base.position.x+5, my_melee_base.position.y+4)
                build_action = BuildAction(EntityType.MELEE_UNIT, position)
            entity_actions[my_melee_base.id] = EntityAction(None, build_action, None, None)

        # ranged bases
        for my_ranged_base in game.my_ranged_bases:
            build_action = None
            if self.can_produce and game.my_resource_count >= 30:
                position = Vec2Int(my_ranged_base.position.x+5, my_ranged_base.position.y+4)
                build_action = BuildAction(EntityType.RANGED_UNIT, position)
            entity_actions[my_ranged_base.id] = EntityAction(None, build_action, None, None)

        # main base
        for my_builder_base in game.my_builder_bases:
            build_action = None
            cond1 = self.can_produce and game.my_resource_count >= 10 and len(game.my_builder_units) <= 40 and (
                len(game.my_builder_units) <= game.my_unit_count // 2 + 2) and (len(game.my_builder_units) <= len(game.resources) // 2)
            cond2 = game.my_resource_count >= 10 and game.my_food_count < 20 and len(game.my_builder_units) <= len(game.resources) // 2
            if cond1 or cond2:
                position = Vec2Int(my_builder_base.position.x+5, my_builder_base.position.y+4)
                build_action = BuildAction(EntityType.BUILDER_UNIT, position)
            entity_actions[my_builder_base.id] = EntityAction(None, build_action, None, None)

    def command_army(self, game, damap, entity_actions):

        for battle_ship in game.my_army:
            cur_pos = battle_ship.position
            move_action = None
            attack_action = None
            move_target = None
            attack_target = None

            if not self.attack_mode:
                move_target = Vec2Int(damap.def_point[0], damap.def_point[1])
            else:
                if len(game.enemy_units) > 0:
                    dist, attack_target, move_target = Calc.find_closest(cur_pos, game.enemy_units, damap.map_size)
                elif len(game.enemy_buildings) > 0:
                    dist, attack_target, move_target = Calc.find_closest(cur_pos, game.enemy_buildings, damap.map_size)
            if move_target is not None:
                move_action = MoveAction(move_target, True, True)
                attack_action = AttackAction(attack_target, AutoAttack(30, []))
            entity_actions[battle_ship.id] = EntityAction(move_action, None, attack_action, None)

        for turret in game.my_turrets:
            attack_action = AttackAction(None, AutoAttack(5, []))
            entity_actions[turret.id] = EntityAction(None, None, attack_action, None)

    def command_build_prod(self, game, damap, entity_actions):

        # repair
        for prod_to_repair in self.prod_in_progress:
            for task in self.prod_buider_tasks:
                if prod_to_repair not in {self.prod_buider_tasks[0][2], self.prod_buider_tasks[1][2]}:
                    if task[1] is not None:
                        if (task[1].position.x == prod_to_repair.position.x) and (task[1].position.y == prod_to_repair.position.y):
                            task[1] = None
                    if task[1] is None and task[2] is None:
                        move_action = None
                        build_action = None
                        repair_action = RepairAction(prod_to_repair.id)
                        move_spot = damap.find_move_spot(task[0].position, prod_to_repair.position, 5)
                        if move_spot is not None:
                            move_action = MoveAction(move_spot, True, False)
                        else:
                            print(f'command_build_prod repair: no move_spot')
                            continue
                        task[2] = prod_to_repair
                        task[3] = move_spot
                        entity_action = EntityAction(move_action, None, None, repair_action)
                        entity_actions[task[0].id] = entity_action

        # build
        if self.need_prod:
            prod_type = None
            if len(game.my_ranged_bases) < 1:
                prod_type = EntityType.RANGED_BASE
            elif len(game.my_melee_bases) < 1:
                prod_type = EntityType.MELEE_BASE
            for task in self.prod_buider_tasks[:1]:
                if task[1] is None and task[2] is None:
                    move_spot = None
                    move_action = None
                    build_action = None
                    repair_action = None
                    prod_spot = damap.find_building_spot(5, task[0].position)
                    if prod_spot is not None:
                        build_action = BuildAction(prod_type, prod_spot)
                        move_spot = damap.find_move_spot(task[0].position, prod_spot, 5)
                        if move_spot is not None:
                            move_action = MoveAction(move_spot, True, False)
                        else:
                            print(f'command_build_prod build: no move_spot')
                            continue
                        task[1] = build_action
                        task[3] = move_spot
                        entity_action = EntityAction(move_action, build_action, None, None)
                        entity_actions[task[0].id] = entity_action

    def command_build_houses(self, game, damap, entity_actions):

        # repair
        for house_to_repair in self.houses_in_progress:
            for num, task in enumerate(self.house_buider_tasks):
                if task[1] is not None and task[2] is None:
                    if (task[1].position.x == house_to_repair.position.x) and (task[1].position.y == house_to_repair.position.y):
                        task[1] = None
                if task[1] is None and task[2] is None and self.need_houses:
                    if num == 0 and self.house_buider_tasks[1][2] is not None:
                        if self.house_buider_tasks[1][2].id == house_to_repair.id:
                            continue
                    elif num == 1 and self.house_buider_tasks[0][2] is not None:
                        if self.house_buider_tasks[0][2].id == house_to_repair.id:
                            continue
                if task[1] is None and task[2] is None:
                    move_action = None
                    build_action = None
                    repair_action = RepairAction(house_to_repair.id)
                    task[2] = house_to_repair
                    move_spot = damap.find_move_spot(task[0].position, house_to_repair.position, 3)
                    if move_spot is not None:
                        move_action = MoveAction(move_spot, True, False)
                    else:
                        print(f'command_build_houses repair: no move_spot')
                        continue
                    task[3] = move_spot
                    entity_action = EntityAction(move_action, None, None, repair_action)
                    entity_actions[task[0].id] = entity_action

        # build
        if self.need_houses:
            for task in self.house_buider_tasks[:2]:
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
                        else:
                            print(f'command_build_houses build: no move_spot')
                            continue
                        task[1] = build_action
                        task[3] = move_spot
                        entity_action = EntityAction(move_action, build_action, None, None)
                        entity_actions[task[0].id] = entity_action

    def command_miners(self, game, damap, entity_actions):

        damap.calc_obtainable_resources()
        for miner in self.my_miners.values():
            move_action = None
            attack_action = None
            cur_pos = miner.pos

            if damap.hmap_enemies[cur_pos.x, cur_pos.y]:
                miner.res = None
                miner.rep = None
                move_action = MoveAction(Vec2Int(5, 5), True, False)
                entity_actions[miner.id] = EntityAction(move_action, None, attack_action, None)
            elif miner.res is None:
                dist, target_res, target_position = Calc.find_closest(cur_pos, damap.obtainable_resources, damap.map_size, game.res_avails)
                move_spot = damap.find_move_spot(cur_pos, target_position, 1)
                if move_spot is not None:
                    move_action = MoveAction(move_spot, True, False)
                else:
                    damap.calc_obtainable_resources()
                    dist, target_res, target_position = Calc.find_closest(cur_pos, damap.obtainable_resources, damap.map_size, game.res_avails)
                    move_spot = damap.find_move_spot(cur_pos, target_position, 1)
                    if move_spot is not None:
                        move_action = MoveAction(move_spot, True, False)
                    else:
                        continue
                game.res_avails[target_res] = False
                miner.res = target_res
                miner.mov = move_spot
                miner.rep = None
                move_action = MoveAction(target_position, True, False)
                attack_action = AttackAction(target_res, None)
                entity_actions[miner.id] = EntityAction(move_action, None, attack_action, None)

    def get_action(self, player_view, debug_interface):
        self.times = 0
        tstmp = time.time()

        entity_actions = {}
        game = Game(player_view.my_id, player_view.players, player_view.current_tick)
        damap = Map(game.parse_entities(player_view.entities, player_view.map_size))
        if not len(game.my_builder_bases):
            return Action(entity_actions)

        try:
            self.precalc(game, damap, entity_actions)
        except Exception as e:
            print(f'precalc: {e}')

        try:
            self.command_prod(game, entity_actions)
        except Exception as e:
            print(f'command_prod: {e}')

        try:
            self.command_army(game, damap, entity_actions)
        except Exception as e:
            print(f'command_army: {e}')

        try:
            self.command_build_prod(game, damap, entity_actions)
        except Exception as e:
            print(f'command_build_prod: {e}')

        try:
            self.command_build_houses(game, damap, entity_actions)
        except Exception as e:
            print(f'command_build_houses: {e}')

        try:
            self.command_miners(game, damap, entity_actions)
        except Exception as e:
            print(f'command_miners: {e}')

        self.times = time.time()-tstmp

        return Action(entity_actions)

    def debug_update(self, player_view, debug_interface):

        debug_interface.send(DebugCommand.Clear())
        debug_interface.send(DebugCommand.Add(DebugData.Log(f'Time: {self.times*1000:.2f}')))
        # if len(self.workers) > 0:
        #     debug_interface.send(DebugCommand.Add(DebugData.Log(f'Workers: {self.workers}')))
        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'can_produce: {self.can_produce}')))
        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'need_houses: {self.need_houses}')))
        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'houses_in_progress: {self.houses_in_progress}')))
        # for task in self.house_buider_tasks:
        #     debug_interface.send(DebugCommand.Add(DebugData.Log(f'house_buider_tasks: {task}')))
        # for key, miner in self.my_miners.items():
        #     debug_interface.send(DebugCommand.Add(DebugData.Log(f'miner {key}: {miner.res, miner.mov}')))
        # debug_interface.send(DebugCommand.Add(DebugData.Log(f'my_miners: {self.my_miners}')))
        debug_interface.get_state()
