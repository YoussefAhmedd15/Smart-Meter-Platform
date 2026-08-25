#
# --------------------------------------------------------------------------
#  Gurux Ltd
#
#
#
# Filename:        $HeadURL$
#
# Version:         $Revision$,
#                  $Date$
#                  $Author$
#
# Copyright (c) Gurux Ltd
#
# ---------------------------------------------------------------------------
#
#  DESCRIPTION
#
# This file is a part of Gurux Device Framework.
#
# Gurux Device Framework is Open Source software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2 of the License.
# Gurux Device Framework is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# More information of Gurux products: https:#www.gurux.org
#
# This code is licensed under the GNU General Public License v2.
# Full text may be retrieved at http:#www.gnu.org/licenses/gpl-2.0.txt
# ---------------------------------------------------------------------------
from .enums.MaximumStringLength import MaximumStringLength


class GXCompressionOptions:
    """
    V.44 compression options.
    """

    def __init__(self):
        self.__enableCompression = False
        self.__defaultCodewordSize = 6
        self.__defaultOrdinalSize = 7
        self.__maxCodewords = 1024
        self.__maximumStringLength = MaximumStringLength.VALUE_255
        self.__maxDictionarySize = 3072

    @property
    def enableCompression(self):
        """
        Is V.44 compression enabled.
        """
        return self.__enableCompression

    @enableCompression.setter
    def enableCompression(self, value):
        self.__enableCompression = bool(value)

    @property
    def defaultCodewordSize(self):
        """
        Default codeword size.
        """
        return self.__defaultCodewordSize

    @defaultCodewordSize.setter
    def defaultCodewordSize(self, value):
        if value < 6 or value > 120:
            raise ValueError("The minimum allowed codeword size is 6 bytes.")
        self.__defaultCodewordSize = value

    @property
    def defaultOrdinalSize(self):
        """
        Default ordinal size.
        """
        return self.__defaultOrdinalSize

    @defaultOrdinalSize.setter
    def defaultOrdinalSize(self, value):
        if value < 7 or value > 8:
            raise ValueError("The orginal size ranges from 7 to 8 bytes.")
        self.__defaultOrdinalSize = value

    @property
    def maxCodewords(self):
        """
        Gets the maximum number of codewords that can be processed.
        """
        return self.__maxCodewords

    @maxCodewords.setter
    def maxCodewords(self, value):
        self.__maxCodewords = value

    @property
    def maximumStringLength(self):
        """
        The maximum string length.
        """
        return self.__maximumStringLength

    @maximumStringLength.setter
    def maximumStringLength(self, value):
        self.__maximumStringLength = value

    @property
    def maxDictionarySize(self):
        """
        Max dictionary size.
        """
        return self.__maxDictionarySize

    @maxDictionarySize.setter
    def maxDictionarySize(self, value):
        self.__maxDictionarySize = value
