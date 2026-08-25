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


class GXCompressionArgs:
    """
    V.44 compression event arguments.
    """

    def __init__(self, operation, options, inputData):
        """
        Constructor.
        """
        self.__operation = operation
        self.__options = options
        self.__inputData = inputData
        self.__outputData = None

    @property
    def operation(self):
        """
        Gets the compression operation to perform.
        """
        return self.__operation

    @property
    def options(self):
        """
        Gets the compression options for the V.44 compression.
        """
        return self.__options

    @property
    def inputData(self):
        """
        Gets the input data that is being compressed or decompressed.
        """
        return self.__inputData

    @property
    def outputData(self):
        """
        Gets the output data produced by the compression or decompression
        operation.
        """
        return self.__outputData

    @outputData.setter
    def outputData(self, value):
        self.__outputData = value
