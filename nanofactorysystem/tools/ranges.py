##########################################################################
# Copyright (c) 2024 Reinhard Caspary                                    #
# <reinhard.caspary@phoenixd.uni-hannover.de>                            #
# This program is free software under the terms of the MIT license.      #
##########################################################################
#
# This module contains the data class Range, which represents a single
# continuous range of float numbers and the class RangeSet, which holds
# a set of non-overlapping Range objects.
#
##########################################################################


class Range:

    """ Data class with attributes low: float and high: float, representing a
    continuous range of numbers. Range objects support the comparisons '<' and
    '>'. Two Range objects can be merged using the method merge(other). """

    low: float
    high: float

    def __init__(self, data):

        """ Initialize a Range object from a (low, high) tuple or list or from
        another Range object. """

        # Data conversion
        if isinstance(data, Range):
            data = (data.low, data.high)
        elif isinstance(data, tuple):
            pass
        elif isinstance(data, list):
            data = tuple(data)
        else:
            raise ValueError(f"Unknown data type '{type(data)}'!")

        # Sanity checks
        assert(len(data) == 2)
        low, high = (float(value) for value in data)
        assert(low < high)

        # Store values
        self.low = low
        self.high = high

    def __lt__(self, other):

        """ Compare with other Range object or suitable tuple or list. The object is
        supposed to be less than other if its values are less and both Range objects
        do not overlap or touch. """
        
        try:
            other = Range(other)
        except:
            return NotImplemented
        
        return self.high < other.low
    
    def __gt__(self, other):

        """ Compare with other Range object or suitable tuple or list. The object is
        supposed to be greater than other if its values are greater and both Range objects
        do not overlap or touch. """

        try:
            other = Range(other)
        except:
            return NotImplemented
        
        return self.low > other.high
            
    def merge(self, other):

        """ Merge other Range object or suitable tuple or list to self. Raise ValueError,
        if both objects do not overlap or touch. """
        
        try:
            other = Range(other)
        except:
            raise TypeError(f"Unknown data type '{type(other)}'!")
        
        if other < self or other > self:
            raise ValueError("No overlap!")
            
        self.low = min(self.low, other.low)
        self.high = max(self.high, other.high)
    
    @property
    def size(self):

        """ Size of the Range object is the positive difference of its values. """
        
        return (self.high - self.low)
    
    def __repr__(self):

        """ Simple representation string of the Range object. """

        return f"Range(({self.low:g},{self.high:g}))"

        
class RangeSet:

    """ This class holds a set of non-overlapping Range objects, each representing a
    continuous range of float numbers. """

    data: set
    
    def __init__(self, data=None):

        """ Initialize a RangeSet object from another RangeSet object, a set or list of Range
        objects or a single Range object or tuple. New Range objects can be added and two RangeSet
        objects can be merged. RangeSet objects provide a number of convenience properties: min,
        max, size, range, sorted, lowest, and highest. """

        # Data conversion
        if data is None:
            data = set()
            # data = {}
        elif isinstance(data, RangeSet):
            data = data.data
        elif isinstance(data, set):
            pass
        elif isinstance(data, list):
            data = set(data)
            # data =
        elif isinstance(data, (Range, tuple)):
            data = {data}
        else:
            raise TypeError(f"Unknown data type '{type(data)}'!")

        # Store data as set of Range objects
        self.data = {Range(item) for item in data}

        # Merge all overlapping ranges
        self._reduce()
    
    def _reduce(self):

        """ Merge all overlapping Range objects in the set. """

        # Nothing to do for empty set or single element
        if len(self) < 2:
            return

        # Save a copy of the current set
        data = set(self.data)

        # Clear and rebuild the current set
        self.data.clear()
        while len(data) > 0:

            # Pick a range from the copy and try to merge it into any other range
            this = data.pop()
            for other in data:
                try:
                    other.merge(this)
                    break
                except ValueError:
                    pass

            # No merge possible -> store this range in the new range set
            else:
                self.data.add(this)

    def __len__(self):

        """ Length of a RangeSet object is its number of Range objects. """

        return len(self.data)

    def __or__(self, other):

        """ Overloaded '|' operator. Return a new RangeSet by merging this with
        another one. """
        
        try:
            other = RangeSet(other)
        except:
            return NotImplemented

        return RangeSet(self.data | other.data)

    def add(self, item):

        """ Add a new Range object to this RangeSet. """

        # Data conversion
        try:
            item = Range(item)
        except ValueError:
            raise TypeError(f"Unknown data type '{type(item)}'!")

        # Add new range to the current set
        self.data |= {item}

        # Merge all overlapping ranges
        self._reduce()

    @property
    def min(self):

        """ Lower limit of the RangeSet: Smallest low attribute of all ranges in the set. """

        if len(self) == 0:
            raise ValueError("No range!")
        return min(item.low for item in self.data)
        
    @property
    def max(self):
        
        """ Upper limit of the RangeSet: Greatest high attribute of all ranges in the set. """

        if len(self) == 0:
            raise ValueError("No range!")
        return max(item.high for item in self.data)
    
    @property
    def size(self):

        """ Difference between the upper and the lower limits of the RangeSet. """

        if len(self) == 0:
            return 0.0
        return (self.max - self.min)
    
    @property
    def range(self):

        """ New range object, which spans the full range of teh RangeSet. """
        
        return Range((self.min, self.max))

    @property
    def sorted(self):

        """ Sorted list of all Range objects in the set. """
        
        return list(sorted(self.data))
    
    @property
    def lowest(self):

        """ Smallest Range object in the set. """

        if len(self) < 1:
            return None
        return self.sorted[0]
    
    @property
    def highest(self):

        """ Greatest Range object in the set. """

        if len(self) < 1:
            return None
        return self.sorted[-1]
    
    def __repr__(self):

        """ Simple representation string of the RangeSet object. """

        if len(self) < 1:
            data = ""
        else:
            data = ",".join([f"({i.low:g},{i.high:g})" for i in self.sorted])
            data = f"[{data}]"
        return f"RangeSet({data})"



if __name__ == "__main__":
    
    item = Range((4,6))
    item1 = Range((2,3))
    print(item)
    ranges = RangeSet(data = item)
    ranges.add(item1)
    print(len(ranges.data))
    print(ranges)
    print(ranges.sorted)
    print(ranges.highest)
