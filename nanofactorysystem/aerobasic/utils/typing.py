from nanofactorysystem.aerobasic.constants import DataItemEnum

QueryItem = str | DataItemEnum
StatusQueryType = tuple[QueryItem] | tuple[QueryItem, QueryItem] | tuple[QueryItem, QueryItem, QueryItem]