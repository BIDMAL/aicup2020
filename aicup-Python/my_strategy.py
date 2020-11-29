import model


class MyStrategy:
    def get_action(self, player_view, debug_interface):
        my_id = player_view.my_id
        resources = []
        builders = []
        for entity in player_view.entities:
            if entity.player_id == my_id:
                if entity.entity_type == 3:
                    builders.append(entity)
                elif entity.entity_type == 8:
                    resources.append(entity)
        for builder in builders:
            cur_pos = builder.position
            min_dist = player_view.map_size**2
            target = cur_pos
            for res in resources:
                cd = (cur_pos.x - res.position.x)**2 + \
                    (cur_pos.y - res.position.y)**2
                if cd < min_dist:
                    min_dist = cd
                    target = res.position
        return model.Action({})

    def debug_update(self, player_view, debug_interface):
        debug_interface.send(model.DebugCommand.Clear())
        debug_interface.get_state()
