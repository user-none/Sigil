/************************************************************************
**
**  Copyright (C) 2009, 2010  Strahinja Markovic
**
**  This file is part of Sigil.
**
**  Sigil is free software: you can redistribute it and/or modify
**  it under the terms of the GNU General Public License as published by
**  the Free Software Foundation, either version 3 of the License, or
**  (at your option) any later version.
**
**  Sigil is distributed in the hope that it will be useful,
**  but WITHOUT ANY WARRANTY; without even the implied warranty of
**  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
**  GNU General Public License for more details.
**
**  You should have received a copy of the GNU General Public License
**  along with Sigil.  If not, see <http://www.gnu.org/licenses/>.
**
*************************************************************************/

#pragma once
#ifndef IMPORTEPUB_H
#define IMPORTEPUB_H

#include "ImportOEBPS.h"

class HTMLResource;
class CSSResource;


class ImportEPUB : public ImportOEBPS
{

public:

    // Constructor;
    // The parameter is the file to be imported
    ImportEPUB( const QString &fullfilepath );

    // Reads and parses the file 
    // and returns the created Book
    virtual QSharedPointer< Book > GetBook();    

private:

    /**
     * Checks for the presence of the encryption.xml file
     * in the META-INF folder.
     *
     * @return \c True when the epub contains encryption.xml
     */
    bool EpubContainsEncryptionXml();

};

#endif // IMPORTEPUB_H

