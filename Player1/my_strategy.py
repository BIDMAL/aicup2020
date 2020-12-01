# import model.
from model import EntityType, Vec2Int, EntityAction, Action, BuildAction, MoveAction, AttackAction, DebugCommand


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
    def find_closest(entity, targets):
        return


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
                if entity.entity_type in [EntityType.MELEE_UNIT, EntityType.RANGED_UNIT, EntityType.TURRET, EntityType.BUILDER_UNIT]:
                    self.enemy_units.append(entity)
                elif entity.entity_type in [EntityType.WALL, EntityType.HOUSE, EntityType.BUILDER_BASE, EntityType.MELEE_BASE, EntityType.RANGED_BASE]:
                    self.enemy_buildings.append(entity)


class MyStrategy:

    def get_action(self, player_view, debug_interface):

        entity_actions = {}
        game = Game(player_view.map_size, player_view.my_id, player_view.players)
        game.parse_entities(player_view.entities)

        my_unit_count = len(game.my_builder_units) + len(game.my_melee_units) + len(game.my_ranged_units)
        my_food_count = 15 + 5*len(game.my_houses)
        my_unit_slots = my_food_count - my_unit_count
        my_army = game.my_melee_units + game.my_ranged_units

        for my_ranged_base in game.my_ranged_bases:
            build_action = None
            if my_unit_slots and game.my_resource_count > 29:
                position = Vec2Int(my_ranged_base.position.x-1, my_ranged_base.position.y)
                build_action = BuildAction(EntityType.BUILDER_UNIT, position)
            entity_actions[my_ranged_base.id] = EntityAction(
                None, build_action, None, None)

        for my_builder_base in game.my_builder_bases:
            build_action = None
            if my_unit_slots and game.my_resource_count > 9:
                position = Vec2Int(my_builder_base.position.x-1, my_builder_base.position.y)
                build_action = BuildAction(EntityType.BUILDER_UNIT, position)
            entity_actions[my_builder_base.id] = EntityAction(None, build_action, None, None)

        for ship in my_army:
            cur_pos = ship.position
            move_action = None
            attack_action = None
            dist = game.map_size**2
            move_target = None
            attack_target = None
            if len(my_army) < 6:
                move_target = Vec2Int(game.my_ranged_bases[0].position.x+4, game.my_ranged_bases[0].position.y+4)
            else:
                if len(game.enemy_units) > 0:
                    for unit in game.enemy_units:
                        cur_dist = (cur_pos.x - unit.position.x)**2 + (cur_pos.y - unit.position.y)**2
                        if cur_dist < dist:
                            dist = cur_dist
                            move_target = unit.position
                            attack_target = unit.id
                            if dist < 2:
                                break
                elif len(game.enemy_buildings) > 0:
                    for building in game.enemy_buildings:
                        cur_dist = (cur_pos.x - building.position.x)**2 + (cur_pos.y - building.position.y)**2
                        if cur_dist < dist:
                            dist = cur_dist
                            move_target = building.position
                            attack_target = building.id
                            if dist < 2:
                                break
            move_action = MoveAction(move_target, True, False)
            attack_action = AttackAction(attack_target, None)
            entity_actions[ship.id] = EntityAction(
                move_action, None, attack_action, None)

        for builder in game.my_builder_units:
            cur_pos = builder.position
            target_res = None
            move_action = None
            attack_action = None
            dist = game.map_size**2
            for res in game.resources:
                if game.res_avails[res.id]:
                    cur_dist = (cur_pos.x - res.position.x)**2 + (cur_pos.y - res.position.y)**2

                    if cur_dist < dist:
                        dist = cur_dist
                        target_res = res.id
                        target_position = res.position
                        if dist < 2:
                            break
            game.res_avails[target_res] = False
            move_action = MoveAction(target_position, True, False)
            attack_action = AttackAction(target_res, None)
            entity_actions[builder.id] = EntityAction(
                move_action, None, attack_action, None)

        # print(f"entity_actions: {entity_actions}")
        return Action(entity_actions)

    def debug_update(self, player_view, debug_interface):
        debug_interface.send(DebugCommand.Clear())
        debug_interface.get_state()
