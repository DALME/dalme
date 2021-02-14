from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from collections import OrderedDict


class DALMELimitOffsetPagination(LimitOffsetPagination):
    """ Subclasses LimitOffsetPagination to add metadata to
    response if requested """

    def get_paginated_response(self, data_object):
        data, queryset, instance = data_object
        response_obj = [
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]

        if self.request.GET.get('meta') is not None:
            response_obj.append(('meta', instance.get_metadata(queryset)))

        return Response(OrderedDict(response_obj))
