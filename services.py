from contrib import endpoints

import api


application = endpoints.api_server([api.MaltioApi],
                                   restricted=False)
