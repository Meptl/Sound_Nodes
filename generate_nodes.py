import bpy

def set_driver(node, path):
    # add new driver
    driver = node.outputs[0].driver_add("default_value")
    driver.driver.expression = "var"

    var = driver.driver.variables.new()
    var.name = "var"
    var.targets[0].id_type = 'SCENE'
    var.targets[0].id = bpy.data.scenes['Scene']
    var.targets[0].data_path = path



def generate_sound_basic():
    # check if group already exists
    if "Sound Info" not in bpy.data.node_groups:
        sound_basic = bpy.data.node_groups.new("Sound Info", "GeometryNodeTree")

        # create group outputs
        group_outputs = sound_basic.nodes.new('NodeGroupOutput')
        group_outputs.location = (300,0)

        sound_basic.interface.new_socket('Loudness', in_out='OUTPUT', socket_type='NodeSocketFloat')

        #loudness
        loudness = sound_basic.nodes.new('ShaderNodeValue')
        loudness.label = 'Loudness'
        loudness.location = (-200,100)
        set_driver(loudness, "sound_nodes[\"loudness\"]")

        # connect
        sound_basic.links.new(loudness.outputs[0], group_outputs.inputs['Loudness'])

        # Frame driver. Forces reevaluation of the node.
        frame = sound_basic.nodes.new('ShaderNodeValue')
        frame.label = 'Frame'
        frame.location = (-200,-200)
        driver = frame.outputs[0].driver_add("default_value")
        driver.driver.expression = "frame"
    else:
        # refresh drivers
        sound_basic = bpy.data.node_groups["Sound Info"]

        # delete old drivers
        sound_basic.animation_data_clear()

        # add new drivers
        for node in sound_basic.nodes:
            if node.label == "Loudness":
                set_driver(node, "sound_nodes[\"loudness\"]")
            elif node.label == "Frame":
                driver = node.outputs[0].driver_add("default_value")
                driver.driver.expression = "frame"


def generate_spectrogram(spect_bins):
    # check if group already exists
    if "Spectrogram" not in bpy.data.node_groups:
        spectrogram = bpy.data.node_groups.new("Spectrogram", "GeometryNodeTree")
        spectrogram.interface.new_socket('index', in_out='INPUT', socket_type='NodeSocketInt')
        spectrogram.interface.new_socket('value', in_out='OUTPUT', socket_type='NodeSocketFloat')
    else:
        spectrogram = bpy.data.node_groups["Spectrogram"]
        for node in spectrogram.nodes:
            spectrogram.nodes.remove(node)

    group_outputs = spectrogram.nodes.new('NodeGroupOutput')
    group_outputs.location = (520,-400)

    group_inputs = spectrogram.nodes.new('NodeGroupInput')
    group_inputs.location = (-170,200)

    accumulator = None
    for i in range(0, spect_bins):
        # Spectrogram Driver node
        node = spectrogram.nodes.new('ShaderNodeValue')
        node.label = str(i)
        node.location = (-200,100 - (i * 100))
        if i < 32:
            set_driver(node, "sound_nodes[\"spectrogram1\"][" + str(i) + "]")
        else:
            set_driver(node, "sound_nodes[\"spectrogram2\"][" + str(i-32) + "]")

        # Compare node to index
        comparison = spectrogram.nodes.new('FunctionNodeCompare')
        comparison.data_type = 'INT'
        comparison.location = (0,50 - (i * 100))
        comparison.operation = 'EQUAL'
        comparison.hide = True
        if i == 0:
            comparison.operation = 'LESS_EQUAL'
        elif i == spect_bins - 1:
            comparison.operation = 'GREATER_EQUAL'
        comparison.inputs[3].default_value = i
        spectrogram.links.new(group_inputs.outputs[0], comparison.inputs[2])

        # Activate or deactivate driver based on comparison
        activator = spectrogram.nodes.new('ShaderNodeMath')
        activator.operation = 'MULTIPLY'
        activator.location = (180,100 - (i * 100))
        activator.hide = True
        spectrogram.links.new(node.outputs[0], activator.inputs[0])
        spectrogram.links.new(comparison.outputs[0], activator.inputs[1])

        if accumulator is None:
            accumulator = activator
        else:
            old_accum = accumulator
            accumulator = spectrogram.nodes.new('ShaderNodeMath')
            accumulator.operation = 'ADD'
            accumulator.location = (360,100 - (i * 100))
            accumulator.hide = True
            spectrogram.links.new(old_accum.outputs[0], accumulator.inputs[0])
            spectrogram.links.new(activator.outputs[0], accumulator.inputs[1])

    # Link the final accum to output
    spectrogram.links.new(accumulator.outputs[0], group_outputs.inputs[0])

    # Frame driver. Forces reevaluation of the node.
    frame = spectrogram.nodes.new('ShaderNodeValue')
    frame.label = 'Frame'
    frame.location = (-400,-200)
    driver = frame.outputs[0].driver_add("default_value")
    driver.driver.expression = "frame"
