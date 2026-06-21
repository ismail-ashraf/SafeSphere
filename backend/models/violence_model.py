import tensorflow as tf

def build_violence_model(model_path: str):
    """بناء معمارية MobileNetV3Small وحمل الأوزان تلقائياً"""
    base_model = tf.keras.applications.MobileNetV3Small(
        input_shape=(224, 224, 3), 
        include_top=False, 
        weights=None
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = base_model(inputs, training=False)
    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dropout(0.5)(x)
    outputs = tf.keras.layers.Dense(2, activation='softmax')(x)
    
    model = tf.keras.Model(inputs, outputs)
    model.load_weights(model_path, by_name=False, skip_mismatch=False)
    return model