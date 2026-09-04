#
#  --------------------------------------------------------------------------
#   Gurux Ltd
#
#
#
#  Filename:        $HeadURL$
#
#  Version:         $Revision$,
#                   $Date$
#                   $Author$
#
#  Copyright (c) Gurux Ltd
#
# ---------------------------------------------------------------------------
#
#   DESCRIPTION
#
#  This file is a part of Gurux Device Framework.
#
#  Gurux Device Framework is Open Source software; you can redistribute it
#  and/or modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; version 2 of the License.
#  Gurux Device Framework is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  More information of Gurux products: http://www.gurux.org
#
#  This code is licensed under the GNU General Public License v2.
#  Full text may be retrieved at http://www.gnu.org/licenses/gpl-2.0.txt
# ---------------------------------------------------------------------------
from gurux_dlms.objects.GXDLMSArrayManagerItem import GXDLMSArrayManagerItem
from .GXDLMSObject import GXDLMSObject
from .IGXDLMSBase import IGXDLMSBase
from ..enums import ErrorCode
from ..internal._GXCommon import _GXCommon
from ..GXByteBuffer import GXByteBuffer
from ..enums import ObjectType, DataType
from ..internal._GXLocalizer import _GXLocalizer
from ..internal._GXDataInfo import _GXDataInfo
from ..ValueEventArgs import ValueEventArgs
from .GXDLMSProfileGeneric import GXDLMSProfileGeneric
from .GXDLMSTargetObject import GXDLMSTargetObject


# pylint: disable=too-many-public-methods
class GXDLMSArrayManager(GXDLMSObject, IGXDLMSBase):
    """
    DLMS/COSEM Array Manager.

    Online help:
    https://www.gurux.fi/Gurux.DLMS.Objects.GXDLMSArrayManager
    """

    def __init__(self, ln="0.0.18.0.0.255", sn=0):
        super().__init__(ObjectType.ARRAY_MANAGER, ln, sn)
        self.elements = []

    def getValues(self):
        return [self.logicalName, self.elements]

    def numberOfEntries(self, client, id_):
        """Returns the number of entries in the selected array."""
        return client.method(self, 1, id_)

    def parseNumberOfEntries(self, reply):
        """Parse number of entries from meter reply."""
        if isinstance(reply, (bytes, bytearray)):
            reply = GXByteBuffer(reply)

        info = _GXDataInfo()
        return int(_GXCommon.getData(None, reply, info))

    def retrieveEntries(self, client, id_, from_, to):
        """Returns entries from the selected range."""
        data = GXByteBuffer()
        data.setUInt8(DataType.STRUCTURE)
        data.setUInt8(2)
        _GXCommon.setData(None, data, DataType.UINT8, id_)
        data.setUInt8(DataType.STRUCTURE)
        data.setUInt8(2)
        _GXCommon.setData(None, data, DataType.UINT16, from_)
        _GXCommon.setData(None, data, DataType.UINT16, to)
        return client.method(self, 2, data.array(), DataType.STRUCTURE)

    def parseEntries(self, reply):
        """Parse returned entries from meter reply."""
        info = _GXDataInfo()
        return _GXCommon.getData(None, reply, info)

    def insertEntry(self, client, id_, index, entry):
        """Insert a new entry."""
        data = self.__build_index_entry_structure(id_, index, entry)
        return client.method(self, 3, data.array(), DataType.STRUCTURE)

    def updateEntry(self, client, id_, index, entry):
        """Update an existing entry."""
        data = self.__build_index_entry_structure(id_, index, entry)
        return client.method(self, 4, data.array(), DataType.STRUCTURE)

    def removeEntries(self, client, id_, from_, to):
        """Remove entries from the selected range."""
        data = GXByteBuffer()
        data.setUInt8(DataType.STRUCTURE)
        data.setUInt8(2)
        _GXCommon.setData(None, data, DataType.UINT8, id_)
        data.setUInt8(DataType.STRUCTURE)
        data.setUInt8(2)
        _GXCommon.setData(None, data, DataType.UINT16, from_)
        _GXCommon.setData(None, data, DataType.UINT16, to)
        return client.method(self, 5, data.array(), DataType.STRUCTURE)

    def __build_index_entry_structure(self, id_, index, entry):
        data = GXByteBuffer()
        data.setUInt8(DataType.STRUCTURE)
        data.setUInt8(2)
        _GXCommon.setData(None, data, DataType.UINT8, id_)
        data.setUInt8(DataType.STRUCTURE)
        data.setUInt8(2)
        _GXCommon.setData(None, data, DataType.UINT16, index)
        _GXCommon.setData(None, data, _GXCommon.getDLMSDataType(type(entry)), entry)
        return data

    # pylint: disable=too-many-function-args
    def invoke(self, settings, e):
        e.byte_array = True
        reply = GXByteBuffer()

        if e.index == 1:
            self.__number_of_entries(settings, e, int(e.parameters), reply)
        elif e.index == 2:
            self.__retrieve_entries(settings, e, e.parameters, reply)
        elif e.index == 3:
            self.__insert_entry(settings, e, e.parameters)
        elif e.index == 4:
            self.__update_entry(settings, e, e.parameters)
        elif e.index == 5:
            self.__remove_entries(settings, e, e.parameters, reply)
        else:
            e.error = ErrorCode.READ_WRITE_DENIED
        return reply.array() if reply.size != 0 else None

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def _get_data(self, settings, target, attribute_index, selector=0, parameters=None):
        if target.get_data_type(attribute_index) == DataType.ARRAY:
            arg = ValueEventArgs(target, attribute_index, selector, parameters)
            value = target.getValue(settings, arg)

            if isinstance(value, (bytes, bytearray)):
                bb = GXByteBuffer(value)
                if bb.getUInt8() == DataType.ARRAY:
                    return bb

        raise ValueError("Target attribute is not an array.")

    def __number_of_entries(self, settings, e, id_, reply):
        found = False
        for item in self.elements:
            if item.id == id_:
                target = item.element.target

                if isinstance(target, GXDLMSProfileGeneric):
                    if item.element.attribute_index == 2:
                        _GXCommon.setData(
                            settings, reply, DataType.UINT32, target.entries_in_use
                        )
                        found = True
                if not found:
                    value = self._get_data(
                        settings, target, item.element.attribute_index
                    )
                    count = _GXCommon.getObjectCount(value)
                    if count <= 0xFF:
                        dt = DataType.UINT8
                    elif count <= 0xFFFF:
                        dt = DataType.UINT16
                    else:
                        dt = DataType.UINT32
                    _GXCommon.setData(settings, reply, dt, count)
                    found = True
                break

        if not found:
            e.error = ErrorCode.READ_WRITE_DENIED

    # pylint: disable=chained-comparison
    def __retrieve_entries(self, settings, e, args, reply):
        found = False
        id_ = int(args[0])
        from_ = int(args[1][0])
        to = int(args[1][1])

        for item in self.elements:
            if item.id == id_ and from_ <= to and from_ > 0:
                parameters = None

                if isinstance(item.element.target, GXDLMSProfileGeneric):
                    parameters = [None, None, from_, to]

                arg = ValueEventArgs(
                    item.element.target, item.element.attribute_index, 2, parameters
                )

                bb = GXByteBuffer(item.element.target.getValue(settings, arg))
                info = _GXDataInfo()
                arr = _GXCommon.getData(settings, bb, info)

                from_ -= 1

                if to < len(arr):
                    del arr[to:]

                if from_ != 0:
                    del arr[:from_]

                _GXCommon.setData(settings, reply, DataType.ARRAY, arr)
                found = True
                break

        if not found:
            e.error = ErrorCode.READ_WRITE_DENIED

    def __insert_entry(self, settings, e, args):
        found = False
        id_ = int(args[0])

        for item in self.elements:
            if item.id == id_:
                index = int(args[1][0])
                value = args[1][1]

                arg = ValueEventArgs(
                    item.element.target, item.element.attribute_index, 0, None
                )

                bb = GXByteBuffer(item.element.target.getValue(settings, arg))
                info = _GXDataInfo()
                arr = _GXCommon.getData(settings, bb, info)

                if index == 0:
                    arr.insert(0, value)
                elif index > len(arr):
                    arr.append(value)
                else:
                    arr.insert(index, value)

                arg.value = arr
                item.element.target.setValue(settings, arg)
                found = True
                break

        if not found:
            e.error = ErrorCode.READ_WRITE_DENIED

    def __update_entry(self, settings, e, args):
        found = False
        id_ = int(args[0])

        for item in self.elements:
            if item.id == id_:
                index = int(args[1][0])
                value = args[1][1]

                if index > 0:
                    index -= 1

                    arg = ValueEventArgs(
                        item.element.target, item.element.attribute_index, 0, None
                    )

                    bb = GXByteBuffer(item.element.target.getValue(settings, arg))
                    info = _GXDataInfo()
                    arr = _GXCommon.getData(settings, bb, info)

                    if index < len(arr):
                        arr[index] = value
                        arg.value = arr
                        item.element.target.setValue(settings, arg)
                        found = True

                break

        if not found:
            e.error = ErrorCode.READ_WRITE_DENIED

    def __remove_entries(self, settings, e, args):
        found = False
        id_ = int(args[0])
        from_ = int(args[1][0])
        to = int(args[1][1])

        if from_ != 0 and from_ <= to:
            for item in self.elements:
                if item.id == id_:
                    arg = ValueEventArgs(
                        item.element.target, item.element.attribute_index, 0, None
                    )

                    bb = GXByteBuffer(item.element.target.getValue(settings, arg))
                    info = _GXDataInfo()
                    arr = _GXCommon.getData(settings, bb, info)

                    from_ -= 1
                    del arr[from_:to]

                    arg.value = arr
                    item.element.target.setValue(settings, arg)
                    found = True
                    break

        if not found:
            e.error = ErrorCode.READ_WRITE_DENIED

    def getAttributeIndexToRead(self, all_):
        attributes = []

        if all_ or not self.logicalName:
            attributes.append(1)

        if all_ or self.canRead(2):
            attributes.append(2)

        return attributes

    def getNames(self):
        return (_GXLocalizer.gettext("Logical name"), _GXLocalizer.gettext("Objects"))

    def getMethodNames(self):
        return (
            _GXLocalizer.gettext("Amount"),
            _GXLocalizer.gettext("Retrieve"),
            _GXLocalizer.gettext("Insert"),
            _GXLocalizer.gettext("Update"),
            _GXLocalizer.gettext("Remove"),
        )

    def getMaxSupportedVersion(self):
        return 0

    def getAttributeCount(self):
        return 2

    def getMethodCount(self):
        return 5

    def getDataType(self, index):
        if index == 1:
            return DataType.OCTET_STRING
        if index == 2:
            return DataType.ARRAY

        raise ValueError("get_data_type failed. Invalid attribute index.")

    #
    # Attribute get/set.
    #
    def getValue(self, settings, e):
        if e.index == 1:
            return _GXCommon.logicalNameToBytes(self.logicalName)

        if e.index == 2:
            data = GXByteBuffer()
            count = len(self.elements) if self.elements else 0

            data.setUInt8(DataType.ARRAY)
            _GXCommon.setObjectCount(count, data)

            for item in self.elements:
                data.setUInt8(DataType.STRUCTURE)
                data.setUInt8(2)

                _GXCommon.setData(settings, data, DataType.UINT8, item.id)

                data.setUInt8(DataType.STRUCTURE)
                data.setUInt8(3)

                _GXCommon.setData(
                    settings, data, DataType.UINT16, item.element.target.object_type
                )
                _GXCommon.setData(
                    settings,
                    data,
                    DataType.OCTET_STRING,
                    _GXCommon.logicalNameToBytes(item.element.target.logicalName),
                )
                _GXCommon.setData(
                    settings, data, DataType.INT8, item.element.attribute_index
                )

            return data.array()

        e.error = ErrorCode.READ_WRITE_DENIED
        return None

    def setValue(self, settings, e):
        # pylint: disable=import-outside-toplevel
        from .._GXObjectFactory import _GXObjectFactory

        if e.index == 1:
            self.logicalName = _GXCommon.toLogicalName(e.value)
        elif e.index == 2:
            self.elements.clear()
            if e.value is not None:
                for tmp in e.value:
                    item_data = list(tmp)
                    item = GXDLMSArrayManagerItem()
                    item.id = int(item_data[0])
                    target_data = item_data[1]
                    object_type = ObjectType(int(target_data[0]))
                    obj = _GXObjectFactory.createObject(object_type)
                    obj.logicalName = _GXCommon.toLogicalName(target_data[1])
                    attribute_index = int(target_data[2])
                    item.element = GXDLMSTargetObject(obj, attribute_index)
                    self.elements.append(item)
        else:
            e.error = ErrorCode.READ_WRITE_DENIED

    def load(self, reader):
        # pylint: disable=import-outside-toplevel
        from .._GXObjectFactory import _GXObjectFactory

        self.elements.clear()
        if reader.is_start_element("Elements", True):
            while reader.is_start_element("Item", True):
                item = GXDLMSArrayManagerItem()
                item.id = int(reader.read_element_content_as_int("Id"))
                if reader.is_start_element("Target", True):
                    object_type = ObjectType(reader.read_element_content_as_int("Type"))
                    obj = _GXObjectFactory.createObject(object_type)
                    obj.logicalName = reader.read_element_content_as_string("LN")
                    index = reader.read_element_content_as_int("Index")
                    item.element = GXDLMSTargetObject(obj, index)
                    reader.read_end_element("Target")
                reader.read_end_element("Item")
                self.elements.append(item)

            reader.read_end_element("Elements")

    def save(self, writer):
        writer.write_start_element("Elements")

        if self.elements:
            for item in self.elements:
                writer.write_start_element("Item")
                writer.write_element_string("Id", item.id)

                writer.write_start_element("Target")
                writer.write_element_string(
                    "Type", int(item.element.target.object_type)
                )
                writer.write_element_string("LN", item.element.target.logicalName)
                writer.write_element_string("Index", item.element.attribute_index)
                writer.write_end_element()

                writer.write_end_element()

        writer.write_end_element()

    def postLoad(self, reader):
        """Update element target objects after XML loading."""
        for item in self.elements:
            if item.element and item.element.target:
                obj = reader.objects.find_by_ln(
                    item.element.target.object_type, item.element.target.logicalName
                )
                if obj is not None:
                    item.element.target = obj
