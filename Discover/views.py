from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import dbhelper
import logging
import json
logger = logging.getLogger('mylogger')
# Create your views here.
def get_travel_note_list(request):
    db = None
    try:
        db = dbhelper.DBHelper()
        index = request.GET.get('page',default=1)
        result = db.get_notes_list(int(index))
        return HttpResponse(result)
    except Exception as e:
        logger.error(e.message)
    finally:
        db.close()

def search_notes(request):
    db = None
    try:
        db = dbhelper.DBHelper()
        search_word = request.GET.get('search_word')
        if not search_word:
            raise Exception()
        else:
            # result = {}
            notes_result = db.search_note(search_word)
            return HttpResponse(json.dumps(notes_result))
            # result['search_word'] = search_word
            # result['content'] = notes_result
            # if result:
            #     return HttpResponse(json.dumps(result))
    except Exception as e:
        return HttpResponse('404 Not Found!!')
    finally:
        db.close()

def to_travel_note(request):
    if request.method == 'GET':
        return render(request, 'Discover/NoteDetail.html')
    else:
        return HttpResponse('404 NOT FOUND!!')

def get_travel_note(request):
    db = None
    try:
        db = dbhelper.DBHelper()
        id = request.GET.get('id')
        if not id:
            raise Exception()
        else:
            result = db.get_note(id)
            if result:
                return HttpResponse(result)
            else:
                raise Exception()
    except Exception as e:
        return HttpResponse('404 Not Found!!')
    finally:
        db.close()
    # except Exception as e:
    #     logger.error(e.message)
    #     return HttpResponse('404 NOT FOUND!!')
    # finally:
    #     db.close()