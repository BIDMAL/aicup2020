from model import Action, EntityAction, BuildAction, MoveAction, AttackAction, RepairAction, AutoAttack
from model import DebugCommand, DebugData
from model import EntityType, Vec2Int


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

    def find_building_spot(self, size):
        start_x = 0
        start_y = 0
        end_x = self.map_size - size
        end_y = self.map_size - size
        increment_x = 1
        increment_y = 1
        half = self.map_size // 2
        if self.def_point is not None:
            if self.def_point[0] > half:
                start_x = self.map_size - size
                end_x = 0
                increment_x = -1
            if self.def_point[0] > half:
                start_y = self.map_size - size
                end_y = 0
                increment_y = -1
        '''
        for z in range(10):
            for i in range(z):
                print(ll[i][z], ll[z][i], end=' ')
            print(ll[z][z])'''
        for z in range(self.map_size - size):
            for xy in range(z):
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

    def parse_entities(self, entities):
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
        free_spots = [[True for _ in range(self.map_size)] for _ in range(self.map_size)]

        for entity in entities:
            if entity.entity_type == EntityType.RESOURCE:
                self.resources.append(entity)
                self.res_avails[entity.id] = True
                free_spots[entity.position.x][entity.position.y] = False
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
                if entity.entity_type in [EntityType.TURRET, EntityType.BUILDER_UNIT, EntityType.MELEE_UNIT, EntityType.RANGED_UNIT]:
                    self.enemy_units.append(entity)
                elif entity.entity_type in [EntityType.WALL, EntityType.HOUSE, EntityType.BUILDER_BASE, EntityType.MELEE_BASE, EntityType.RANGED_BASE]:
                    self.enemy_buildings.append(entity)

            if entity.entity_type in [EntityType.WALL, EntityType.BUILDER_UNIT, EntityType.MELEE_UNIT, EntityType.RANGED_UNIT]:
                free_spots[entity.position.x][entity.position.y] = False
            elif entity.entity_type == EntityType.TURRET:
                for i in range(2):
                    for j in range(2):
                        free_spots[entity.position.x+i][entity.position.y+j] = False
            elif entity.entity_type == EntityType.HOUSE:
                for i in range(3):
                    for j in range(3):
                        free_spots[entity.position.x+i][entity.position.y+j] = False
            elif entity.entity_type in [EntityType.BUILDER_BASE, EntityType.MELEE_BASE, EntityType.RANGED_BASE]:
                for i in range(5):
                    for j in range(5):
                        free_spots[entity.position.x+i][entity.position.y+j] = False

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
        return free_spots, self.def_point


class MyStrategy:

    def get_action(self, player_view, debug_interface):

        entity_actions = {}
        game = Game(player_view.map_size, player_view.my_id, player_view.players)
        damap = Map(game.parse_entities(player_view.entities))

        for my_ranged_base in game.my_ranged_bases:
            build_action = None
            if game.free_unit_slots and game.my_resource_count >= 30:
                position = Vec2Int(my_ranged_base.position.x+game.orientation[0], my_ranged_base.position.y+game.orientation[1])
                build_action = BuildAction(EntityType.RANGED_UNIT, position)
            entity_actions[my_ranged_base.id] = EntityAction(None, build_action, None, None)

        for my_builder_base in game.my_builder_bases:
            build_action = None
            if game.free_unit_slots and game.my_resource_count >= 10 and len(game.my_builder_units) <= game.my_food_count // 3:
                position = Vec2Int(my_builder_base.position.x+game.orientation[0], my_builder_base.position.y+game.orientation[1])
                build_action = BuildAction(EntityType.BUILDER_UNIT, position)
            entity_actions[my_builder_base.id] = EntityAction(None, build_action, None, None)

        for battle_ship in game.my_army:
            cur_pos = battle_ship.position
            move_action = None
            attack_action = None
            move_target = None
            attack_target = None
            if len(game.my_army) < 5 and len(game.my_ranged_bases) > 0 and len(game.my_builder_units) > 0:
                move_target = Vec2Int(game.def_point[0], game.def_point[1])
            else:
                if len(game.enemy_units) > 0:
                    dist, attack_target, move_target = Calc.find_closest(cur_pos, game.enemy_units, game.map_size**2)
                elif len(game.enemy_buildings) > 0:
                    dist, attack_target, move_target = Calc.find_closest(cur_pos, game.enemy_buildings, game.map_size**2)
            if move_target is not None:
                move_action = MoveAction(move_target, True, False)
                attack_action = AttackAction(attack_target, AutoAttack(3, []))
            entity_actions[battle_ship.id] = EntityAction(move_action, None, attack_action, None)

        house_to_repair = None
        for house in game.my_houses:
            if not house.active:
                house_to_repair = house
                break
        dedicated_builder = 0
        if game.my_unit_count >= 15:
            dedicated_builder = 1

        if (house_to_repair is not None) or (game.free_unit_slots <= 1 and len(game.my_builder_units)):
            dedicated_builder = 1
            builder = game.my_builder_units[0]
            move_spot = None
            move_action = None
            build_action = None
            repair_action = None
            if house_to_repair is not None:
                repair_action = RepairAction(house_to_repair.id)
                move_spot = damap.find_move_spot(builder.position, house_to_repair.position, 2)
                if move_spot is not None:
                    move_action = MoveAction(move_spot, True, False)
                entity_actions[builder.id] = EntityAction(move_action, None, None, repair_action)
            else:
                house_spot = damap.find_building_spot(3)
                if house_spot is not None:
                    build_action = BuildAction(EntityType.HOUSE, house_spot)
                    move_spot = damap.find_move_spot(builder.position, house_spot, 3)
                    if move_spot is not None:
                        move_action = MoveAction(move_spot, True, False)
                    entity_actions[builder.id] = EntityAction(move_action, build_action, None, None)

        for builder in game.my_builder_units[dedicated_builder:]:
            cur_pos = builder.position
            move_action = None
            attack_action = None
            dist, target_res, target_position = Calc.find_closest(cur_pos, game.resources, game.map_size**2, game.res_avails)
            game.res_avails[target_res] = False
            move_action = MoveAction(target_position, True, False)
            attack_action = AttackAction(target_res, None)
            entity_actions[builder.id] = EntityAction(move_action, None, attack_action, None)

        return Action(entity_actions)

    def debug_update(self, player_view, debug_interface):
        debug_interface.send(DebugCommand.Clear())
        debug_interface.get_state()
