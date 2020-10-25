from .base import BaseParser

PARSER_MODULE_MAP = {
    '.dot': '_dot',
}
CLS_BASE_PARSER = BaseParser


def get_graph_parser(parser_type):
    """Get an instance of graph parser dynamically.

    Parameters
    ----------
    parser_type : str
        Type of parser.

    Returns
    -------
    parser : an sublcass instance of `BaseParser`
    """
    import importlib, sys
    from pathlib import Path

    if parser_type not in PARSER_MODULE_MAP:
        raise ValueError(f'unsupported parser for {parser_type}')

    submodule_name = PARSER_MODULE_MAP[parser_type]
    module_name = f'{__name__}.{submodule_name}'

    this_dir = Path(__file__).parent
    fn_parser = this_dir.joinpath(f'{submodule_name}.py')

    spec = importlib.util.spec_from_file_location(module_name, fn_parser)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules[module_name] = mod

    parser_name = getattr(mod, 'PARSER_IMPL')
    if parser_name is None:
        candidates = [v for v in dir(mod) if (
            v.endswith('Parser') and v != CLS_BASE_PARSER.__name__
        )]
        assert len(candidates) == 1, (
            'Failed to find valid graph parser class, this might be an '
            'implementation error.'
        )
        cls_parser = getattr(mod, candidates[0])
    else:
        cls_parser = getattr(mod, parser_name)

    assert issubclass(cls_parser, CLS_BASE_PARSER), (
        f'Type of imported `parser` should be a subclass of {CLS_BASE_PARSER}, '
        'this might be an implementation error.'
    )
    return cls_parser()


__all__ = ['get_graph_parser']
