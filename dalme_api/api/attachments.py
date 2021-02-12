from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser, FormParser, MultiPartParser
from dalme_api.serializers import AttachmentSerializer
from dalme_app.models import Attachment
from dalme_api.access_policies import AttachmentAccessPolicy


class Attachments(viewsets.ModelViewSet):
    """ API endpoint for managing attachments """
    permission_classes = (AttachmentAccessPolicy,)
    parser_classes = (MultiPartParser, FormParser, FileUploadParser,)
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    def create(self, request, format=None):
        try:
            new_obj = Attachment()
            new_obj.file = request.data['file']
            new_obj.save()
            result = {'id': new_obj.id}
            status = 201
        except Exception as e:
            result = {'error': 'There was an error processing the file: ' + str(e)}
            status = 400
        return Response(result, status)
