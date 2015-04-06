#!/usr/bin/python
from __future__ import print_function, division
import sys
import click
import fionautil.layer
from . import svg
from . import layer as Layer


@click.group()
def main():
    pass


@main.command()
@click.argument('layer', default=sys.stdin, type=click.File('r'))
@click.argument('output', required=None, default=sys.stdout, type=click.File('w'))
@click.option('-f', '--scale', type=int)
def rescale(layer, output, scale):
    '''Rescale an SVG by a factor'''
    result = svg.rescale(layer, scale)
    click.echo(result, file=output)


@main.command()
@click.argument('layer', default=sys.stdin, type=click.File('r'))
@click.argument('output', required=None, default=sys.stdout, type=click.File('w'))
@click.option('-s', '--style', type=str, help="Style string to append to SVG")
def addstyle(layer, output, style):
    '''Add a CSS string to an SVG's style attribute'''
    result = svg.add_style(layer, style)
    click.echo(result, file=output)


@main.command()
@click.argument('layer', default='/dev/stdin')
@click.argument('output', required=None, default=sys.stdout, type=click.File('w'))
@click.option('--minx', '-w', type=float, required=None)
@click.option('--maxx', '-w', type=float, required=None)
@click.option('--miny', '-s', type=float, required=None)
@click.option('--maxy', '-n', type=float, required=None)
@click.option('--scale', '-c', type=int, default='100')
def draw(layer, output, minx=None, maxx=None, miny=None, maxy=None, scale=None):
    '''Draw a geodata layer to a simple SVG'''
    scale = scale or 1

    mbr = (minx, maxx, miny, maxy)

    result = Layer.compose(layer, mbr, scalar=(1 / scale))

    click.echo(result, file=output)
