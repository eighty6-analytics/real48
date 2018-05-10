'''Unpack Borland Pascal 6-byte "real48" floating point number.

Author: David Bowe
Date: 2018-05-09

Python Version: 3.6

References:
    Martin Bless (mb), m.bless at gmx.de, 2001-12-16
    Tilman, http://siarp.de/node/191, 24-01-2009

In the context of this program the data structure of a
real48 number is assumed to be a 6 byte string ('r48'):

r48[0]  r48[1]   r48[2]   r48[3]   r48[4]   r48[5]
a0      a1       a2       a3       a4       a5
sffffff ffffffff ffffffff ffffffff ffffffff eeeeeeee

s=sign (1 bit), f=mantisse (39 bit), e=exponent (8 bit, bias 129)
order: S-F-E

An exponent of zero also signals an overall value of zero
'''

import struct

def combine_ints(int2: int, int4: int):
    '''Combine 2 byte and 4 byte ints into 6 byte real48

    Decimal numbers are stored within the Pervasice SQL database
    of Iris Exchequer with two integers of 2 bytes and 4 bytes.
    These must be combined and then reversed to form a real48 float.
    '''
    if -32767 <= int2 <= 32767 and -2147483648 <= int4 <= 2147483647:
      small = struct.pack('>h', int2)                                                                                                                                          
      big = struct.pack('>i', int4)
      r48 = big + small
      return r48
    else:
      raise ValueError('The arguments provided are not within the required range')

class real48:
    def __init__(self, r48: bytes):
        '''Expects a 6 byte string

        sign: Positive or negative value
        mant: Mantissa/significand
        exp: Exponent
        '''
        if type(r48) != bytes:
            raise TypeError('Supplied argument is not a byte string')
        if len(r48) != 6:
            raise FloatingPointError('The supplied byte string does not contain 6 bytes')

        self.byte_str = r48
        self.sign = self.__extract_sign__(self.byte_str)
        self.exp = self.__extract_exponent__(self.byte_str)

    def __extract_sign__(self, r48):
        '''Determine value of sign bit
        '''
        return (r48[0] & 0x80) >> 7

    def __extract_exponent__(self, r48):
        '''Determine value of exponent
        '''
        return r48[5]

    def reverse_bytes(self):
        '''Reverse byte string
        '''
        self.byte_str = self.byte_str[::-1]
        self.sign = self.__extract_sign__(self.byte_str)
        self.exp = self.__extract_exponent__(self.byte_str)
        

    def to_single(self):
        '''Convert r48 to single float via bitwise operations and struct
    
        IEEE Standard 754 defines single floating point numbers as 4 bytes
        
        f[0]     f[1]     f[2]     f[3]
        a0       a1       a2       a3
        seeeeeee efffffff ffffffff ffffffff

        s=sign (1 bit), f=mantisse (23 bit), e=exponent (8 bit, bias 127)
        order: S-E-F

        See header comments for real48 type structure
        sign: Positive or negative value
        mant: Mantissa/significand
        exp: Exponent
        '''
        # Determine mantissa
        mant = ((self.byte_str[0] % 0x80) << 16) \
            + (self.byte_str[1] << 8) \
            + (self.byte_str[2])
    
        if self.exp == 0:
            return 0.0
        if self.exp == 255:
           # TODO: Raise infinite number warning
           # raise ValueError('Numbers should be of finite value')
           pass
    
        # Calculate unbias exponent (127 - 129 = -2)
        unbias_exp = self.exp - 2
    
        # Create bit array (Python displays as int)
        bits = (self.sign << 31) + (unbias_exp << 23) + mant
    
        # Create byte string from int
        reformed_byte_str = struct.pack('>I', bits)
        # Convert byte string to float
        single = struct.unpack('>f', reformed_byte_str)[0]
        return single
       
    
    def to_double(self):
        '''Convert r48 to double float via bitwise operations and struct
    
        IEEE Standard 754 defines double floating point numbers as 8 bytes
        
        d[0]     d[1]     d[2]     d[3]
        a0       a1       a2       a3
        seeeeeee eeefffff ffffffff ffffffff
        ------------------------------------
        d[4]     [5]      d[6]     d[7]
        a4       a5       a6       a7
        ffffffff ffffffff ffffffff ffffffff

        s=sign (1 bit), f=mantisse (52 bit), e=exponent (11 bit, bias 1023)
        order: S-E-F
    
        See header comments for real48 type structure
        sign: Positive or negative value
        mant: Mantissa/significand
        exp: Exponent
        '''
        # Determine mantissa
        mant = ((self.byte_str[0] % 0x80) << 32) \
            + (self.byte_str[1] << 24) \
            + (self.byte_str[2] << 16) \
            + (self.byte_str[3] << 8) \
            + (self.byte_str[4])
    
        if self.exp == 0:
            return 0.0
        if self.exp == 255:
           # TODO: Raise infinite number warning
           # raise ValueError('Numbers should be of finite value')
           pass
    
        # Calculate unbias exponent (1023 - 129 = 894)
        unbias_exp = self.exp + 894
    
        # Create bit array (Python displays as int)
        bits = (self.sign << 63) + (unbias_exp << 52) + (mant << 13)
    
        # Create byte string from int
        reformed_byte_str = struct.pack('>Q', bits)
        # Convert byte string to float
        double = struct.unpack('>d', reformed_byte_str)[0]
        return double


    def value(self):
        '''Interprets provided byte string through byte structure

        Much slower implementation then coverting to single or double
        '''
        a0,a1,a2 = self.byte_str[0], self.byte_str[1], self.byte_str[2]
        a3,a4,a5 = self.byte_str[3], self.byte_str[4], self.byte_str[5]

        # Determine value of sign bit
        sign = int(a0/128)

        # Remove exponent bias
        exp = a5 - 129

        # Check for zero exponent
        if a5 == 0:
            mant = 0.0
        else:
            mant = 1.0 + ( 2.0 * ((a0 % 128)+(a1+(a2+(a3+a4/256.0)/256.0)/256.0)/256.0)/256.0 )

        if sign == 1:
            mant = -mant
        value = 2.0**exp * mant
        return value
        
