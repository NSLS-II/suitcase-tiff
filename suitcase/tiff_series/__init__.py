from tifffile import TiffWriter
import event_model
import numpy
from suitcase import tiff_stack
from ._version import get_versions

__version__ = get_versions()['version']
del get_versions


def export(gen, directory, file_prefix='{start[uid]}-', bigtiff=False,
           byteorder=None, imagej=False, **kwargs):
    """
    Export a stream of documents to a series of TIFF files.

    This creates a file named:
    ``<directory>/<file_prefix>{stream_name}-{field}-{image_number}.tiff``
    for every Event stream and field that contains 2D 'image like' data.

    .. warning::

        This process explicitly ignores all data that is not 2D and does not
        include any metadata in the output file.

    .. note::

        This can alternatively be used to write data to generic buffers rather
        than creating files on disk. See the documentation for the
        ``directory`` parameter below.

    Parameters
    ----------
    gen : generator
        expected to yield ``(name, document)`` pairs

    directory : string, Path or Manager.
        For basic uses, this should be the path to the output directory given
        as a string or Path object. Use an empty string ``''`` to place files
        in the current working directory.

        In advanced applications, this may direct the serialized output to a
        memory buffer, network socket, or other writable buffer. It should be
        an instance of ``suitcase.utils.MemoryBufferManager`` and
        ``suitcase.utils.MultiFileManager`` or any object implementing that
        inferface. See the suitcase documentation (LINK ONCE WRITTEN) for
        details.

    file_prefix : str, optional
        The first part of the filename of the generated output files. This
        string may include templates as in
        ``{start[proposal_id]}-{start[sample_name]}-``, which are populated
        from the RunStart(start), descriptor(descriptor) or event(event)
        documents. The default value is ``{start[uid]}-`` which is guaranteed
        to be present and unique. A more descriptive value depends on the
        application and is therefore left to the user.

    bigtiff : boolean, optional
        Passed into ``tifffile.TiffWriter``. Default False.

    byteorder : string or None, optional
        Passed into ``tifffile.TiffWriter``. Default None.

    imagej: boolean, optional
        Passed into ``tifffile.TiffWriter``. Default False.

    **kwargs : kwargs
        kwargs to be passed to ``tifffile.TiffWriter.save``.

    Returns
    -------
    dest : dict
        dict mapping the 'labels' to lists of file names

    Examples
    --------

    Generate files with unique-identifer names in the current directory.

    >>> export(gen, '')

    Generate files with more readable metadata in the file names.

    >>> export(gen, '', '{start[plan_name]}-{start[motors]}-')

    Include the experiment's start time formatted as YY-MM-DD_HH-MM.

    >>> export(gen, '', '{start[time]:%Y-%m-%d_%H:%M}-')

    Place the files in a different directory, such as on a mounted USB stick.

    >>> export(gen, '/path/to/my_usb_stick')
    """
    with Serializer(directory, file_prefix,
                    bigtiff=bigtiff,
                    byteorder=byteorder,
                    imagej=imagej,
                    **kwargs) as serializer:
        for item in gen:
            serializer(*item)

    return serializer.artifacts


class Serializer(tiff_stack.Serializer):
    """
    Serialize a stream of documents to a series of TIFF files.

    This creates a file named:
    ``<directory>/<file_prefix>{stream_name}-{field}-{image_number}.tiff``
    for every Event stream and field that contains 2D 'image like' data.

    .. warning::

        This process explicitly ignores all data that is not 2D and does not
        include any metadata in the output file.


    .. note::

        This can alternatively be used to write data to generic buffers rather
        than creating files on disk. See the documentation for the
        ``directory`` parameter below.

    Parameters
    ----------
    directory : string, Path or Manager.
        For basic uses, this should be the path to the output directory given
        as a string or Path object. Use an empty string ``''`` to place files
        in the current working directory.

        In advanced applications, this may direct the serialized output to a
        memory buffer, network socket, or other writable buffer. It should be
        an instance of ``suitcase.utils.MemoryBufferManager`` and
        ``suitcase.utils.MultiFileManager`` or any object implementing that
        inferface. See the suitcase documentation (LINK ONCE WRITTEN) for
        details.

    file_prefix : str, optional
        The first part of the filename of the generated output files. This
        string may include templates as in
        ``{start[proposal_id]}-{start[sample_name]}-``, which are populated
        from the RunStart(start), descriptor(descriptor) or event(event)
        documents. The default value is ``{start[uid]}-`` which is guaranteed
        to be present and unique. A more descriptive value depends on the
        application and is therefore left to the user.

    bigtiff : boolean, optional
        Passed into ``tifffile.TiffWriter``. Default False.

    byteorder : string or None, optional
        Passed into ``tifffile.TiffWriter``. Default None.

    imagej: boolean, optional
        Passed into ``tifffile.TiffWriter``. Default False.

    **kwargs : kwargs
        kwargs to be passed to ``tifffile.TiffWriter.save``.
    """
    def event_page(self, doc):
        '''Converts an 'event_page' doc to 'event' docs for processing.

        Parameters:
        -----------
        doc : dict
            Event_Page document
        '''

        events = event_model.unpack_event_page(doc)
        for event_doc in events:
            self.event(event_doc)

    def event(self, doc):
        '''Add event document information to a ".tiff" file.

        This method adds event document information to a ".tiff" file,
        creating it if nesecary.

        .. warning::

            All non 2D 'image like' data is explicitly ignored.

        .. note::

            The data in Events might be structured as an Event, an EventPage,
            or a "bulk event" (deprecated). The DocumentRouter base class takes
            care of first transforming the other repsentations into an
            EventPage and then routing them through here, as we require Event
            documents _in this case_ we overwrite both the `event` method and
            the `event_page` method so we can assume we will always receive an
            Event.

        Parameters:
        -----------
        doc : dict
            Event document
        '''
        event_model.verify_filled(event_model.pack_event_page(*[doc]))
        descriptor = self._descriptors[doc['descriptor']]
        streamname = descriptor.get('name')
        for field in doc['data']:
            img = doc['data'][field]
            # check that the data is 2D, if not ignore it
            img_asarray = numpy.asarray(img)
            if img_asarray.ndim == 2:
                # template the file name.
                self._templated_file_prefix = self._file_prefix.format(
                    start=self._start, descriptor=descriptor,
                    event=doc)
                if not (self._counter.get(streamname, {}).get(field) or
                        self._counter.get(streamname, {}).get(field)
                        == 0):
                    self._counter[streamname][field] = 0
                else:
                    self._counter[streamname][field] += 1
                num = self._counter[streamname][field]
                filename = (f'{self._templated_file_prefix}'
                            f'{streamname}-{field}-{num}.tiff')
                file = self._manager.open('stream_data', filename, 'xb')
                tw = TiffWriter(file, **self._init_kwargs)
                self._tiff_writers[streamname][field+f'-{num}'] = tw
                tw.save(img_asarray, *self._kwargs)
