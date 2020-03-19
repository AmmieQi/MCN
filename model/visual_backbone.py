from keras.layers import Conv2D, Add, ZeroPadding2D, ReLU,UpSampling2D,Flatten, Concatenate, MaxPooling2D,Multiply,Input,Lambda,Dense,Dropout,Dot,Reshape,Activation,GlobalAveragePooling2D,AveragePooling2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.normalization import BatchNormalization
from keras.regularizers import l2
from utils.utils import compose
from functools import wraps

@wraps(Conv2D)
def DarknetConv2D(*args, **kwargs):
    """Wrapper to set Darknet parameters for Convolution2D."""
    darknet_conv_kwargs = {'kernel_regularizer': l2(5e-4)}
    darknet_conv_kwargs['padding'] = 'valid' if kwargs.get('strides')==(2,2) else 'same'
    darknet_conv_kwargs.update(kwargs)
    return Conv2D(*args, **darknet_conv_kwargs)

def DarknetConv2D_BN_Leaky(*args, **kwargs):
    """Darknet Convolution2D followed by BatchNormalization and LeakyReLU."""
    no_bias_kwargs = {'use_bias': False}
    no_bias_kwargs.update(kwargs)
    return compose(
        DarknetConv2D(*args, **no_bias_kwargs),
        BatchNormalization(),
        LeakyReLU(alpha=0.1))
def VGGnetConv2D(*args, **kwargs):
    """Wrapper to set Darknet parameters for Convolution2D."""
    darknet_conv_kwargs = {'kernel_regularizer': l2(5e-4)}
    darknet_conv_kwargs['padding'] = 'valid' if kwargs.get('strides')==(2,2) else 'same'
    darknet_conv_kwargs.update(kwargs)
    return Conv2D(*args, **darknet_conv_kwargs)
def VGGnetConv2D_BN_Relu(*args, **kwargs):
    """Darknet Convolution2D followed by BatchNormalization and LeakyReLU."""
    no_bias_kwargs = {'use_bias': True}
    no_bias_kwargs.update(kwargs)
    return compose(
        VGGnetConv2D(*args, **no_bias_kwargs),
        ReLU())

def vgg16(inputs):
    stage1=compose(
        VGGnetConv2D_BN_Relu(64,(3,3)),
        VGGnetConv2D_BN_Relu(64, (3, 3)),
        MaxPooling2D(),
        VGGnetConv2D_BN_Relu(128, (3, 3)),
        VGGnetConv2D_BN_Relu(128, (3, 3)),
        MaxPooling2D(),
        VGGnetConv2D_BN_Relu(256, (3, 3)),
        VGGnetConv2D_BN_Relu(256, (3, 3)),
        VGGnetConv2D_BN_Relu(256, (3, 3)),
        MaxPooling2D(),
        VGGnetConv2D_BN_Relu(512, (3, 3)),
        VGGnetConv2D_BN_Relu(512, (3, 3)),
        VGGnetConv2D_BN_Relu(512, (3, 3)),
    )(inputs)
    stage2=compose(
        MaxPooling2D(),
        VGGnetConv2D_BN_Relu(512, (3, 3)),
        VGGnetConv2D_BN_Relu(512, (3, 3)),
        VGGnetConv2D_BN_Relu(512, (3, 3))
    )(stage1)
    stage3=MaxPooling2D()(stage2)
    stage3 = compose(
        VGGnetConv2D_BN_Relu(512, (1,1)),
        VGGnetConv2D_BN_Relu(1024, (3,3)),
        VGGnetConv2D_BN_Relu(512, (1,1)),
        VGGnetConv2D_BN_Relu(1024, (3,3)),
        VGGnetConv2D_BN_Relu(512, (1,1)),
        VGGnetConv2D_BN_Relu(1024, (3, 3)))(stage3)
    return [stage3,stage2,stage1]
def resblock_body(x, num_filters, num_blocks):
    '''A series of resblocks starting with a downsampling Convolution2D'''
    # Darknet uses left and top padding instead of 'same' mode
    x = ZeroPadding2D(((1,0),(1,0)))(x)
    x = DarknetConv2D_BN_Leaky(num_filters, (3,3), strides=(2,2))(x)
    for i in range(num_blocks):
        y = compose(
                DarknetConv2D_BN_Leaky(num_filters//2, (1,1)),
                DarknetConv2D_BN_Leaky(num_filters, (3,3)))(x)
        x = Add()([x,y])
    return x

def darknet_body(x):
    '''Darknent body having 52 Convolution2D layers'''
    x = DarknetConv2D_BN_Leaky(32, (3,3))(x)
    x = resblock_body(x, 64, 1)
    x = resblock_body(x, 128, 2)
    x = resblock_body(x, 256, 8)
    x = resblock_body(x, 512, 8)
    x = resblock_body(x, 1024, 4)
    x = compose(
            DarknetConv2D_BN_Leaky(512, (1,1)),
            DarknetConv2D_BN_Leaky(1024, (3,3)),
            DarknetConv2D_BN_Leaky(512, (1,1)),
            DarknetConv2D_BN_Leaky(1024, (3,3)),
            DarknetConv2D_BN_Leaky(512, (1,1)),
        DarknetConv2D_BN_Leaky(1024, (3, 3)))(x)
    return x

def darknet_resblock(x,num_filters):
    y = compose(
        DarknetConv2D_BN_Leaky(num_filters, (1, 1)),
        DarknetConv2D_BN_Leaky(num_filters*2, (3, 3)))(x)
    x=Add()([x,y])
    return x