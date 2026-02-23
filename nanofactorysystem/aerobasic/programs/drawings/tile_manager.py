"""
TileManager Module
==================
Provides tile-based subdivision of structures for stitched fabrication.

Classes:
    - PlotSettings: Configuration for visualization parameters
    - TilePlotter: Handles all tile visualization
    - TileManager: Manages tile subdivision and provides plotting interface

Tile Counting Convention:
    - Tile (0,0) is at BOTTOM-LEFT of the structure
    - X-index increases left to right
    - Y-index increases bottom to top

    Example for 4x3 grid:
        -----------------------
        | 0,2 | 1,2 | 2,2 | 3,2 |  <- Top row (j=2)
        -----------------------
        | 0,1 | 1,1 | 2,1 | 3,1 |  <- Middle row (j=1)
        -----------------------
        | 0,0 | 1,0 | 2,0 | 3,0 |  <- Bottom row (j=0)
        -----------------------
          ^                   ^
        Left                Right
        (i=0)               (i=3)

Author: Hannes Robben
Date: 2025
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Union, Literal
from nanofactorysystem.devices.coordinate_system import Point3D, Point2D


# ============== Data Classes ==============
@dataclass
class PlotSettings:
    """
    Configuration class for tile visualization settings.

    All sizes are in points (for fonts) or relative units.
    Colors can be any matplotlib-compatible color specification.

    Attributes:
        figsize_overview: Figure size for overview plots (width, height) in inches
        figsize_detail: Figure size for single tile detail plots
        dpi: Resolution for saved figures

        Font settings:
            title_fontsize: Title font size
            label_fontsize: Axis label font size
            tick_fontsize: Tick label font size
            annotation_fontsize: Annotation text font size
            info_box_fontsize: Info box text font size
            tile_index_fontsize: Tile index label font size

        Marker settings:
            tile_center_marker: Marker style for tile centers
            tile_center_size: Marker size for tile centers
            tile_center_width: Line width for tile center markers
            structure_center_marker: Marker style for structure centers
            structure_center_size: Size for structure center markers
            global_center_marker: Marker for global structure center
            global_center_size: Size for global center marker

        Line settings:
            fov_linewidth: Line width for FOV rectangles
            structure_linewidth: Line width for structure boundaries
            boundary_linewidth: Line width for boundary lines

        Colors:
            color_fov_full: Color for full FOV rectangle
            color_fov_usable: Color for usable FOV area
            color_structure: Color for structure area
            color_tile_center: Color for tile center markers
            color_structure_center: Color for structure center markers
            color_global_center: Color for global structure center
            color_boundary_x: Color for X-boundary lines
            color_boundary_y: Color for Y-boundary lines
            color_offset_arrow: Color for offset arrows

        Alpha (transparency) settings:
            alpha_fov_full: Transparency for full FOV
            alpha_fov_usable: Transparency for usable FOV
            alpha_structure: Transparency for structure area
            alpha_boundary: Transparency for boundary lines

        Display toggles:
            show_fov_full: Show full FOV rectangle
            show_fov_usable: Show usable FOV rectangle
            show_structure_area: Show structure area
            show_tile_centers: Show tile center markers
            show_structure_centers: Show structure center markers
            show_boundaries: Show boundary lines
            show_tile_indices: Show tile index labels
            show_offset_arrows: Show offset arrows in detail view
            show_dimensions: Show dimension annotations
            show_info_box: Show info box in detail view
            show_grid: Show plot grid
            show_legend: Show legend
    """
    # Figure settings
    figsize_overview: Tuple[float, float] = (14, 10)
    figsize_detail: Tuple[float, float] = (10, 10)
    dpi: int = 150

    # Font sizes
    title_fontsize: int = 12
    label_fontsize: int = 11
    tick_fontsize: int = 10
    annotation_fontsize: int = 10
    info_box_fontsize: int = 9
    tile_index_fontsize: int = 9

    # Marker settings
    tile_center_marker: str = '+'
    tile_center_size: int = 10
    tile_center_width: float = 2.0
    structure_center_marker: str = 'x'
    structure_center_size: int = 8
    structure_center_width: float = 2.0
    global_center_marker: str = '*'
    global_center_size: int = 15

    # Line widths
    fov_linewidth: float = 1.5
    structure_linewidth: float = 2.5
    boundary_linewidth: float = 1.5

    # Colors
    color_fov_full: str = 'gray'
    color_fov_usable: str = 'blue'
    color_structure: str = 'red'
    color_tile_center: str = 'blue'
    color_structure_center: str = 'red'
    color_global_center: str = 'green'
    color_boundary_x: str = 'red'
    color_boundary_y: str = 'orange'
    color_offset_arrow: str = 'green'
    color_total_structure: str = 'black'

    # Alpha values
    alpha_fov_full: float = 0.2
    alpha_fov_usable: float = 0.4
    alpha_structure: float = 0.3
    alpha_boundary: float = 0.7
    alpha_total_structure: float = 0.3

    # Display toggles
    show_fov_full: bool = True
    show_fov_usable: bool = True
    show_structure_area: bool = True
    show_tile_centers: bool = True
    show_structure_centers: bool = True
    show_boundaries: bool = True
    show_tile_indices: bool = True
    show_offset_arrows: bool = True
    show_dimensions: bool = True
    show_info_box: bool = True
    show_grid: bool = True
    show_legend: bool = True

    # Color scheme presets
    _color_schemes: Dict = field(default_factory=lambda: {
        'default': {
            'color_fov_full': 'gray',
            'color_fov_usable': 'blue',
            'color_structure': 'red',
            'color_tile_center': 'blue',
            'color_structure_center': 'red',
            'color_global_center': 'green',
        },
        'print_friendly': {
            'color_fov_full': '#666666',
            'color_fov_usable': '#1f77b4',
            'color_structure': '#d62728',
            'color_tile_center': '#1f77b4',
            'color_structure_center': '#d62728',
            'color_global_center': '#2ca02c',
        },
        'colorblind_safe': {
            'color_fov_full': '#999999',
            'color_fov_usable': '#0072B2',
            'color_structure': '#D55E00',
            'color_tile_center': '#0072B2',
            'color_structure_center': '#D55E00',
            'color_global_center': '#009E73',
        }
    })

    def apply_color_scheme(self, scheme: Literal['default', 'print_friendly', 'colorblind_safe']):
        """Apply a predefined color scheme."""
        if scheme not in self._color_schemes:
            raise ValueError(f"Unknown color scheme: {scheme}. "
                             f"Available: {list(self._color_schemes.keys())}")
        for key, value in self._color_schemes[scheme].items():
            setattr(self, key, value)

    def update(self, **kwargs):
        """Update multiple settings at once."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"PlotSettings has no attribute '{key}'")


# ============== TilePlotter Class ==============

class TilePlotter:
    """
    Handles visualization of tile subdivisions.

    This class is responsible for all plotting operations related to
    TileManager visualizations. It maintains a reference to the TileManager
    and uses PlotSettings for visual configuration.

    Attributes:
        tile_manager: Reference to the parent TileManager instance
        settings: PlotSettings instance for visual configuration
    """

    def __init__(self, tile_manager: 'TileManager', settings: Optional[PlotSettings] = None):
        """
        Initialize TilePlotter.

        Args:
            tile_manager: The TileManager instance to visualize
            settings: Optional PlotSettings instance. If None, uses defaults.
        """
        self.tile_manager = tile_manager
        self.settings = settings if settings is not None else PlotSettings()

    def update_settings(self, **kwargs):
        """
        Update plot settings.

        Args:
            **kwargs: Setting names and their new values

        Example:
            plotter.update_settings(title_fontsize=14, show_grid=False)
        """
        self.settings.update(**kwargs)

    def apply_color_scheme(self, scheme: str):
        """
        Apply a predefined color scheme.

        Args:
            scheme: One of 'default', 'print_friendly', 'colorblind_safe'
        """
        self.settings.apply_color_scheme(scheme)

    def plot_overview(self,
                      figsize: Optional[Tuple[float, float]] = None,
                      save_path: Optional[str] = None) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot overview of all tiles.

        Shows the complete tile subdivision with:
        - Total structure outline
        - All tiles with their FOV and structure areas
        - Tile centers and structure centers
        - Tile indices

        Args:
            figsize: Optional figure size override
            save_path: Optional path to save the figure

        Returns:
            Tuple of (Figure, Axes)
        """
        tm = self.tile_manager
        s = self.settings

        if tm.tiles is None:
            raise RuntimeError("Tiles not generated. Call calc_parameters() and generate_tiles() first.")

        fig, ax = plt.subplots(figsize=figsize or s.figsize_overview)

        # Total structure background
        struct_rect = patches.Rectangle(
            (tm.center_point[0] - tm.structure_size[0] / 2,
             tm.center_point[1] - tm.structure_size[1] / 2),
            tm.structure_size[0], tm.structure_size[1],
            linewidth=s.structure_linewidth,
            edgecolor=s.color_total_structure,
            facecolor='lightgray',
            alpha=s.alpha_total_structure,
            label='Total Structure',
            zorder=1
        )
        ax.add_patch(struct_rect)

        # Color map for tiles
        colors = plt.cm.Set3(np.linspace(0, 1, len(tm.tiles)))

        for idx, tile in enumerate(tm.tiles):
            i, j = tile['index']
            center = tile['center_tile']

            # Full FOV (dashed)
            if s.show_fov_full:
                fov_rect = patches.Rectangle(
                    (center[0] - tm.fov[0] / 2, center[1] - tm.fov[1] / 2),
                    tm.fov[0], tm.fov[1],
                    linewidth=s.fov_linewidth,
                    edgecolor=s.color_fov_full,
                    facecolor='none',
                    linestyle='--',
                    alpha=0.5,
                    zorder=2
                )
                ax.add_patch(fov_rect)

            # Usable FOV
            if s.show_fov_usable:
                fov_use_rect = patches.Rectangle(
                    (center[0] - tm.fov_use[0] / 2, center[1] - tm.fov_use[1] / 2),
                    tm.fov_use[0], tm.fov_use[1],
                    linewidth=s.fov_linewidth,
                    edgecolor=s.color_fov_usable,
                    facecolor=colors[idx],
                    alpha=s.alpha_fov_usable,
                    zorder=3
                )
                ax.add_patch(fov_use_rect)

            # Structure area within tile
            if s.show_structure_area:
                sb = tile['structure_bounds_absolute']
                struct_width = sb['x_max'] - sb['x_min']
                struct_height = sb['y_max'] - sb['y_min']
                struct_rect = patches.Rectangle(
                    (sb['x_min'], sb['y_min']),
                    struct_width, struct_height,
                    linewidth=s.structure_linewidth,
                    edgecolor=s.color_structure,
                    facecolor=s.color_structure,
                    alpha=s.alpha_structure,
                    zorder=4
                )
                ax.add_patch(struct_rect)

            # Tile center
            if s.show_tile_centers:
                ax.plot(center[0], center[1],
                        s.tile_center_marker,
                        color=s.color_tile_center,
                        markersize=s.tile_center_size,
                        markeredgewidth=s.tile_center_width,
                        zorder=5)

            # Structure center
            if s.show_structure_centers:
                ax.plot(tile['center_structure'][0], tile['center_structure'][1],
                        s.structure_center_marker,
                        color=s.color_structure_center,
                        markersize=s.structure_center_size,
                        markeredgewidth=s.structure_center_width,
                        zorder=5)

            # Tile index label
            if s.show_tile_indices:
                ax.text(center[0], center[1] + tm.fov_use[1] * 0.3,
                        f'({i},{j})',
                        ha='center', va='bottom',
                        fontsize=s.tile_index_fontsize,
                        fontweight='bold',
                        zorder=6)

        # Global structure center
        ax.plot(tm.center_point[0], tm.center_point[1],
                s.global_center_marker,
                color=s.color_global_center,
                markersize=s.global_center_size,
                label='Structure Center',
                zorder=7)

        # Legend
        if s.show_legend:
            legend_elements = [
                patches.Patch(facecolor='lightgray', edgecolor=s.color_total_structure,
                              linewidth=2, alpha=s.alpha_total_structure, label='Total Structure'),
                patches.Patch(facecolor='none', edgecolor=s.color_fov_full,
                              linestyle='--', label='FOV (full)'),
                patches.Patch(facecolor=s.color_fov_usable, edgecolor=s.color_fov_usable,
                              alpha=s.alpha_fov_usable, label='FOV (usable)'),
                patches.Patch(facecolor=s.color_structure, edgecolor=s.color_structure,
                              alpha=s.alpha_structure, label='Structure in Tile'),
                plt.Line2D([0], [0], marker=s.tile_center_marker, color=s.color_tile_center,
                           linestyle='None', markersize=s.tile_center_size, label='Tile Center'),
                plt.Line2D([0], [0], marker=s.structure_center_marker, color=s.color_structure_center,
                           linestyle='None', markersize=s.structure_center_size, label='Structure Center (Tile)'),
                plt.Line2D([0], [0], marker=s.global_center_marker, color=s.color_global_center,
                           linestyle='None', markersize=s.global_center_size, label='Structure Center (Global)')
            ]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=s.annotation_fontsize)

        ax.set_aspect('equal')
        if s.show_grid:
            ax.grid(True, alpha=0.3)
        ax.set_xlabel('X [µm]', fontsize=s.label_fontsize)
        ax.set_ylabel('Y [µm]', fontsize=s.label_fontsize)
        ax.tick_params(labelsize=s.tick_fontsize)
        ax.set_title(f'Tile Overview\n'
                     f'Structure: {tm.structure_size[0]:.0f}×{tm.structure_size[1]:.0f} µm | '
                     f'FOV: {tm.fov[0]:.0f}×{tm.fov[1]:.0f} µm | '
                     f'Usable: {tm.usable_fraction[0] * 100:.0f}% | '
                     f'Tiles: {int(tm.n_tiles[0])}×{int(tm.n_tiles[1])}',
                     fontsize=s.title_fontsize)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=s.dpi, bbox_inches='tight')

        return fig, ax

    def plot_tile(self,
                  tile_id: Union[int, Tuple[int, int]],
                  figsize: Optional[Tuple[float, float]] = None,
                  save_path: Optional[str] = None) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot detailed view of a single tile.

        Shows tile-relative coordinates with:
        - Full and usable FOV
        - Structure boundaries
        - Center points and offset arrows
        - Dimension annotations
        - Info box with tile parameters

        Args:
            tile_id: Either linear index (int) or tuple index (i, j)
            figsize: Optional figure size override
            save_path: Optional path to save the figure

        Returns:
            Tuple of (Figure, Axes)
        """
        tm = self.tile_manager
        s = self.settings

        if tm.tiles is None:
            raise RuntimeError("Tiles not generated. Call calc_parameters() and generate_tiles() first.")

        # Get tile by index
        tile = self._get_tile_by_id(tile_id)
        if tile is None:
            raise ValueError(f"Tile {tile_id} not found.")

        fig, ax = plt.subplots(figsize=figsize or s.figsize_detail)

        center = tile['center_tile']
        i, j = tile['index']

        # All coordinates relative to tile center (0, 0)

        # Full FOV (dashed)
        if s.show_fov_full:
            fov_rect = patches.Rectangle(
                (-tm.fov[0] / 2, -tm.fov[1] / 2),
                tm.fov[0], tm.fov[1],
                linewidth=s.fov_linewidth,
                edgecolor=s.color_fov_full,
                facecolor='lightgray',
                linestyle='--',
                alpha=s.alpha_fov_full,
                label='FOV (full)',
                zorder=1
            )
            ax.add_patch(fov_rect)

        # Usable FOV
        if s.show_fov_usable:
            fov_use_rect = patches.Rectangle(
                (-tm.fov_use[0] / 2, -tm.fov_use[1] / 2),
                tm.fov_use[0], tm.fov_use[1],
                linewidth=s.fov_linewidth,
                edgecolor=s.color_fov_usable,
                facecolor='lightblue',
                alpha=s.alpha_fov_usable,
                label='FOV (usable)',
                zorder=2
            )
            ax.add_patch(fov_use_rect)

        # Structure area
        if s.show_structure_area:
            sb = tile['structure_bounds_relative']
            struct_width = sb['x_max'] - sb['x_min']
            struct_height = sb['y_max'] - sb['y_min']
            struct_rect = patches.Rectangle(
                (sb['x_min'], sb['y_min']),
                struct_width, struct_height,
                linewidth=s.structure_linewidth,
                edgecolor=s.color_structure,
                facecolor='salmon',
                alpha=s.alpha_structure + 0.1,
                label='Structure Area',
                zorder=3
            )
            ax.add_patch(struct_rect)

        # Tile center at (0, 0)
        if s.show_tile_centers:
            ax.plot(0, 0,
                    s.tile_center_marker,
                    color=s.color_tile_center,
                    markersize=s.tile_center_size * 2,
                    markeredgewidth=s.tile_center_width * 1.5,
                    label='Tile Center',
                    zorder=5)

        # Structure center (with offset)
        offset = tile['offset_structure']
        if s.show_structure_centers:
            ax.plot(offset[0], offset[1],
                    s.structure_center_marker,
                    color=s.color_structure_center,
                    markersize=s.structure_center_size * 1.5,
                    markeredgewidth=s.structure_center_width * 1.5,
                    label=f'Structure Center\n(Offset: {offset[0]:.2f}, {offset[1]:.2f})',
                    zorder=5)

        # Offset arrow
        if s.show_offset_arrows and np.any(offset != 0):
            ax.annotate('', xy=(offset[0], offset[1]), xytext=(0, 0),
                        arrowprops=dict(arrowstyle='->', color=s.color_offset_arrow, lw=2),
                        zorder=4)

        # Boundary lines
        if s.show_boundaries:
            sb = tile['structure_bounds_relative']
            ax.axvline(sb['x_min'], color=s.color_boundary_x, linestyle=':',
                       alpha=s.alpha_boundary, label='X-Boundaries', zorder=3)
            ax.axvline(sb['x_max'], color=s.color_boundary_x, linestyle=':',
                       alpha=s.alpha_boundary, zorder=3)
            ax.axhline(sb['y_min'], color=s.color_boundary_y, linestyle=':',
                       alpha=s.alpha_boundary, label='Y-Boundaries', zorder=3)
            ax.axhline(sb['y_max'], color=s.color_boundary_y, linestyle=':',
                       alpha=s.alpha_boundary, zorder=3)

        # Dimension annotations
        if s.show_dimensions:
            sb = tile['structure_bounds_relative']
            struct_width = sb['x_max'] - sb['x_min']
            struct_height = sb['y_max'] - sb['y_min']

            # Structure width
            y_pos = sb['y_min'] - tm.fov[1] * 0.08
            ax.annotate('', xy=(sb['x_max'], y_pos), xytext=(sb['x_min'], y_pos),
                        arrowprops=dict(arrowstyle='<->', color='darkred', lw=1.5))
            ax.text((sb['x_min'] + sb['x_max']) / 2, y_pos - tm.fov[1] * 0.05,
                    f'Structure: {struct_width:.2f} µm',
                    ha='center', fontsize=s.annotation_fontsize, color='darkred')

            # FOV width
            y_pos2 = -tm.fov[1] / 2 - tm.fov[1] * 0.08
            ax.annotate('', xy=(tm.fov_use[0] / 2, y_pos2), xytext=(-tm.fov_use[0] / 2, y_pos2),
                        arrowprops=dict(arrowstyle='<->', color=s.color_fov_usable, lw=1.5))
            ax.text(0, y_pos2 - tm.fov[1] * 0.05,
                    f'FOV usable: {tm.fov_use[0]:.2f} µm',
                    ha='center', fontsize=s.annotation_fontsize, color=s.color_fov_usable)

        # Info box
        if s.show_info_box:
            border_info = tile['is_border']
            border_str = []
            if border_info['left']:
                border_str.append('Left')
            if border_info['right']:
                border_str.append('Right')
            if border_info['bottom']:
                border_str.append('Bottom')
            if border_info['top']:
                border_str.append('Top')
            border_text = ', '.join(border_str) if border_str else 'Inner Tile'

            sb = tile['structure_bounds_relative']
            struct_width = sb['x_max'] - sb['x_min']
            struct_height = sb['y_max'] - sb['y_min']

            info_text = (
                f"Tile ({i}, {j})\n"
                f"Position: {border_text}\n"
                f"─────────────────────\n"
                f"Tile Center (abs): ({center[0]:.2f}, {center[1]:.2f})\n"
                f"Structure Offset: ({offset[0]:.2f}, {offset[1]:.2f})\n"
                f"Direction Factor: ({tile['direction'][0]:.0f}, {tile['direction'][1]:.0f})\n"
                f"─────────────────────\n"
                f"Structure Size: {struct_width:.2f} × {struct_height:.2f} µm\n"
                f"FOV usable: {tm.fov_use[0]:.2f} × {tm.fov_use[1]:.2f} µm\n"
                f"Border Length: {tm.length_border_tiles[0]:.2f} × {tm.length_border_tiles[1]:.2f} µm"
            )

            props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
                    fontsize=s.info_box_fontsize,
                    verticalalignment='top', fontfamily='monospace', bbox=props)

        ax.set_aspect('equal')
        if s.show_grid:
            ax.grid(True, alpha=0.3)
        ax.set_xlabel('X relative to Tile Center [µm]', fontsize=s.label_fontsize)
        ax.set_ylabel('Y relative to Tile Center [µm]', fontsize=s.label_fontsize)
        ax.tick_params(labelsize=s.tick_fontsize)
        ax.set_title(f'Detail View Tile ({i}, {j})', fontsize=s.title_fontsize)

        # Axis limits with margin
        margin = tm.fov[0] * 0.3
        ax.set_xlim(-tm.fov[0] / 2 - margin, tm.fov[0] / 2 + margin)
        ax.set_ylim(-tm.fov[1] / 2 - margin, tm.fov[1] / 2 + margin)

        if s.show_legend:
            ax.legend(loc='upper right', fontsize=s.annotation_fontsize)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=s.dpi, bbox_inches='tight')

        return fig, ax

    def _get_tile_by_id(self, tile_id: Union[int, Tuple[int, int]]) -> Optional[Dict]:
        """
        Get tile by linear index or (i, j) tuple.

        Args:
            tile_id: Linear index (int) or index tuple (i, j)

        Returns:
            Tile dictionary or None if not found
        """
        tiles = self.tile_manager.tiles

        if isinstance(tile_id, int):
            if 0 <= tile_id < len(tiles):
                return tiles[tile_id]
            return None
        elif isinstance(tile_id, tuple) and len(tile_id) == 2:
            for tile in tiles:
                if tile['index'] == tile_id:
                    return tile
            return None
        else:
            raise TypeError(f"tile_id must be int or tuple(int, int), got {type(tile_id)}")


# ============== TileManager Class ==============

class TileManager:
    """
    Manages tile-based subdivision of structures for stitched fabrication.

    This class calculates how to divide a structure larger than the field of view
    into multiple tiles that can be fabricated sequentially. It handles:
    - Calculation of required number of tiles
    - Border tile dimensions (partial filling)
    - Tile center positions
    - Structure boundaries within each tile

    Tile Counting Convention:
        - Tile (0,0) is at BOTTOM-LEFT
        - i increases left to right (X direction)
        - j increases bottom to top (Y direction)

    Attributes:
        center: Center point of the structure (Point2D or Point3D)
        center_point: Center as numpy array [x, y]
        structure_size: Total structure dimensions [width, height]
        fov: Full field of view [width, height]
        fov_use: Usable field of view after overlap [width, height]
        usable_fraction: Fraction of FOV that is usable [x_fraction, y_fraction]
        n_tiles: Number of tiles in each direction [n_x, n_y]
        length_border_tiles: Size of border tile content [width, height]
        offset_border_tiles: Offset of structure in border tiles [x, y]
        tiles: List of tile dictionaries after generate_tiles()
        plotter: TilePlotter instance for visualization

    Example:
        # >>> tm = TileManager(
        # ...     structure_size=(250, 200),
        # ...     fov=100,
        # ...     usable_fraction=0.8
        # ... )
        # >>> tm.calc_parameters()
        # >>> tiles = tm.generate_tiles()
        # >>> tm.plot_overview()
        # >>> tm.plot_tile((0, 0))  # Plot bottom-left corner tile
    """

    def __init__(self,
                 structure_size: Union[Tuple[float, float], List[float]],
                 fov: Union[Tuple[float, float], float, int],
                 usable_fraction: Union[float, int, Tuple[float, float]],
                 center: Union[Point2D, Point3D] = None,
                 plot_settings: Optional[PlotSettings] = None):
        """
        Initialize TileManager.

        Args:
            structure_size: Total structure dimensions (width, height) in µm
            fov: Field of view. Single value for square FOV, or (width, height)
            usable_fraction: Usable fraction of FOV.
                - float (0-1): Same fraction for both axes
                - int (0-100): Interpreted as percentage
                - tuple: Different fractions for (x, y)
            center: Center point of structure. Defaults to (0, 0, 0)
            plot_settings: Optional PlotSettings for visualization
        """
        # Default center
        if center is None:
            center = Point3D(X=0, Y=0, Z=0)

        self.center = center
        self.center_point = np.array((center.X, center.Y))
        self.structure_size = np.array(structure_size)

        # Parse FOV
        if isinstance(fov, tuple):
            self.fov = np.array(fov)
        elif isinstance(fov, (float, int)):
            self.fov = np.array((float(fov), float(fov)))
        else:
            raise TypeError('fov must be tuple or float|int')

        # Parse usable fraction
        if isinstance(usable_fraction, float):
            self.usable_fraction = np.array((usable_fraction, usable_fraction))
        elif isinstance(usable_fraction, int):
            self.usable_fraction = np.array((float(usable_fraction) / 100,
                                             float(usable_fraction) / 100))
        elif isinstance(usable_fraction, tuple):
            self.usable_fraction = np.array(usable_fraction)
        else:
            raise TypeError("usable_fraction must be float, int or tuple(float, float).")

        # Calculate usable FOV
        self.fov_use = self.fov * self.usable_fraction

        # Initialize calculated parameters
        self.n_tiles = None
        self.length_border_tiles = None
        self.offset_border_tiles = None
        self.tiles = None

        # Initialize plotter
        self.plotter = TilePlotter(self, plot_settings)

    def to_json(self) -> dict:
        """Serialize TileManager to JSON-compatible dictionary."""

        # Basic class identification
        result = {
            "__class__": self.__class__.__name__,
        }

        # === INIT PARAMETERS (for reconstruction) ===
        result["__init__"] = {
            # Structure dimensions [width, height]
            "structure_size": self.structure_size.tolist(),

            # Field of view [width, height] or single value
            "fov": self.fov.tolist(),

            # Usable fraction [x_fraction, y_fraction]
            "usable_fraction": self.usable_fraction.tolist(),

            # Center point as serializable format
            "center": self.center.to_json() if hasattr(self.center, 'to_json') else {
                "X": self.center.X,
                "Y": self.center.Y,
                "Z": getattr(self.center, 'Z', 0)
            }
        }

        # === CALCULATED PARAMETERS (state after calc_parameters) ===
        if self.n_tiles is not None:
            result["calculated"] = {
                # Number of tiles [n_x, n_y]
                "n_tiles": self.n_tiles.tolist(),

                # Size of content in border tiles [width, height]
                "length_border_tiles": self.length_border_tiles.tolist(),

                # Offset of structure center in border tiles [x, y]
                "offset_border_tiles": self.offset_border_tiles.tolist(),

                # Usable FOV after overlap [width, height]
                "fov_use": self.fov_use.tolist(),

                # Total number of tiles
                "n_tiles_total": self.get_n_tiles_total()
            }

        # === TILES DATA (state after generate_tiles) ===
        if self.tiles is not None:
            result["tiles"] = []
            for tile in self.tiles:
                tile_data = {
                    # Tile position indices (i, j)
                    "index": tile["index"],

                    # Absolute position of tile center [x, y]
                    "center_tile": tile["center_tile"].tolist(),

                    # Position relative to structure center [x, y]
                    "center_tile_relative": tile["center_tile_relative"].tolist(),

                    # Absolute position of structure center in this tile [x, y]
                    "center_structure": tile["center_structure"].tolist(),

                    # Offset from tile center to structure center [x, y]
                    "offset_structure": tile["offset_structure"].tolist(),

                    # Direction factors [x_dir, y_dir]
                    "direction": tile["direction"].tolist(),

                    # Border flags
                    "is_border": tile["is_border"],

                    # Structure boundaries relative to tile center
                    "structure_bounds_relative": tile["structure_bounds_relative"],

                    # Structure boundaries in absolute coordinates
                    "structure_bounds_absolute": tile["structure_bounds_absolute"]
                }
                result["tiles"].append(tile_data)

        return result

    def _create_direction_grid(self, n_x: int, n_y: int) -> np.ndarray:
        """
        Create grid of direction factors for border tiles.

        Direction factors indicate how structure content is offset:
        - +1: Border on this side (content shifted inward)
        - -1: Border on opposite side (content shifted inward)
        - 0: Inner tile (no offset)

        Args:
            n_x: Number of tiles in X direction
            n_y: Number of tiles in Y direction

        Returns:
            Array of shape (n_y, n_x, 2) with direction factors [x, y]
        """
        # X: +1 at left edge, -1 at right edge, 0 in between
        x_vals = np.zeros(n_x)
        x_vals[0] = 1
        if n_x > 1:
            x_vals[-1] = -1

        # Y: +1 at bottom edge, -1 at top edge, 0 in between
        y_vals = np.zeros(n_y)
        y_vals[0] = 1
        if n_y > 1:
            y_vals[-1] = -1

        x_grid = np.broadcast_to(x_vals, (n_y, n_x))
        y_grid = np.broadcast_to(y_vals[:, np.newaxis], (n_y, n_x))

        return np.stack([x_grid, y_grid], axis=-1)

    def get_fov(self) -> np.ndarray:
        """Get usable FOV dimensions."""
        return self.fov_use

    def get_usable_fraction(self) -> np.ndarray:
        """Get usable fraction of FOV."""
        return self.usable_fraction

    def get_structure_size(self) -> np.ndarray:
        """Get total structure size."""
        return self.structure_size

    def needs_stitching(self) -> bool:
        """
        Check if structure requires stitching (multiple tiles).

        Returns:
            True if structure is larger than usable FOV in any dimension
        """
        return np.any(self.structure_size > self.fov_use)

    def calc_parameters(self):
        """
        Calculate tile subdivision parameters.

        Computes:
        - n_tiles: Number of tiles needed in each direction
        - length_border_tiles: Content size in border tiles
        - offset_border_tiles: Offset of structure center in border tiles
        """
        # Number of tiles needed
        self.n_tiles = np.ceil(self.structure_size / self.fov_use)

        # Length of content in border tiles
        # Total structure minus inner tiles, divided by 2 for each border
        self.length_border_tiles = (self.structure_size - (self.n_tiles - 2) * self.fov_use) / 2

        # Offset of structure center from tile center in border tiles
        self.offset_border_tiles = self.fov_use / 2 - self.length_border_tiles / 2

    def generate_tiles(self) -> List[Dict]:
        """
        Generate all tiles with their properties.

        Returns a list of tile dictionaries, each containing:
        - index: (i, j) tile indices
        - center_tile: Absolute position of tile center
        - center_tile_relative: Position relative to structure center
        - center_structure: Absolute position of structure center in this tile
        - offset_structure: Offset from tile center to structure center
        - direction: Direction factors for this tile
        - is_border: Dict with border flags (left, right, bottom, top)
        - structure_bounds_relative: Boundaries relative to tile center (0,0)
        - structure_bounds_absolute: Boundaries in absolute coordinates

        Returns:
            List of tile dictionaries
        """
        if self.n_tiles is None:
            self.calc_parameters()

        tiles = []
        n_x, n_y = int(self.n_tiles[0]), int(self.n_tiles[1])

        # Starting point (bottom-left tile center)
        start_point = self.center_point - (self.fov_use * (self.n_tiles - 1) / 2)

        # Direction grid for border handling
        direction_grid = self._create_direction_grid(n_x, n_y)

        # Iterate over tiles: j (Y) then i (X)
        for j in range(n_y):
            for i in range(n_x):
                # Tile center in absolute coordinates
                center_tile = start_point + np.array((i, j)) * self.fov_use

                # Tile center relative to structure center
                center_tile_relative = center_tile - self.center_point

                # Direction factors for this tile
                direction = direction_grid[j, i].copy()

                # Offset from tile center to structure content center
                offset_structure = direction * self.offset_border_tiles

                # Structure center in absolute coordinates
                center_structure = center_tile + offset_structure

                # Border flags
                is_border = {
                    'left': (i == 0),
                    'right': (i == n_x - 1),
                    'bottom': (j == 0),
                    'top': (j == n_y - 1)
                }

                # Calculate structure boundaries relative to tile center
                # X boundaries
                if is_border['left']:
                    x_min = offset_structure[0] - self.length_border_tiles[0] / 2
                    x_max = offset_structure[0] + self.length_border_tiles[0] / 2
                elif is_border['right']:
                    x_min = offset_structure[0] - self.length_border_tiles[0] / 2
                    x_max = offset_structure[0] + self.length_border_tiles[0] / 2
                else:
                    x_min = -self.fov_use[0] / 2
                    x_max = self.fov_use[0] / 2

                # Y boundaries
                if is_border['bottom']:
                    y_min = offset_structure[1] - self.length_border_tiles[1] / 2
                    y_max = offset_structure[1] + self.length_border_tiles[1] / 2
                elif is_border['top']:
                    y_min = offset_structure[1] - self.length_border_tiles[1] / 2
                    y_max = offset_structure[1] + self.length_border_tiles[1] / 2
                else:
                    y_min = -self.fov_use[1] / 2
                    y_max = self.fov_use[1] / 2

                tile = {
                    'index': (i, j),
                    'center_tile': center_tile.copy(),
                    'center_tile_relative': center_tile_relative.copy(),
                    'center_structure': center_structure.copy(),
                    'offset_structure': offset_structure.copy(),
                    'direction': direction.copy(),
                    'is_border': is_border,
                    'structure_bounds_relative': {
                        'x_min': x_min,
                        'x_max': x_max,
                        'y_min': y_min,
                        'y_max': y_max
                    },
                    'structure_bounds_absolute': {
                        'x_min': center_tile[0] + x_min,
                        'x_max': center_tile[0] + x_max,
                        'y_min': center_tile[1] + y_min,
                        'y_max': center_tile[1] + y_max
                    }
                }
                tiles.append(tile)

        self.tiles = tiles
        return tiles

    def get_tile(self, tile_id: Union[int, Tuple[int, int]]) -> Optional[Dict]:
        """
        Get a specific tile by index.

        Args:
            tile_id: Linear index (int) or tuple index (i, j)

        Returns:
            Tile dictionary or None if not found
        """
        if self.tiles is None:
            return None

        if isinstance(tile_id, int):
            if 0 <= tile_id < len(self.tiles):
                return self.tiles[tile_id]
            return None
        elif isinstance(tile_id, tuple):
            for tile in self.tiles:
                if tile['index'] == tile_id:
                    return tile
            return None
        return None

    def get_n_tiles_total(self) -> int:
        """Get total number of tiles."""
        if self.n_tiles is None:
            return 0
        return int(self.n_tiles[0] * self.n_tiles[1])

    def get_tile_dict(self) -> List[Dict]:
        """
        Important information:
        tile['center_tile'] -> X and Y coordinates of center of the tile in respect to whole structure
        tile["structure_bounds_relative"] -> Dict of ['x_min'] ['x_max'] ['y_min'] ['y_max'] for relative structure
                                            bounds
        """
        if self.tiles is not None and self.tiles is not {}:
            return self.tiles
        else:
            return self.generate_tiles()

    # ==================== Plotting Interface ====================

    def plot_overview(self,
                      figsize: Optional[Tuple[float, float]] = None,
                      save_path: Optional[str] = None) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot overview of all tiles.

        Delegates to TilePlotter.plot_overview().
        See TilePlotter.plot_overview() for details.
        """
        return self.plotter.plot_overview(figsize=figsize, save_path=save_path)

    def plot_tile(self,
                  tile_id: Union[int, Tuple[int, int]],
                  figsize: Optional[Tuple[float, float]] = None,
                  save_path: Optional[str] = None) -> Tuple[plt.Figure, plt.Axes]:
        """
        Plot detailed view of a single tile.

        Delegates to TilePlotter.plot_tile().
        See TilePlotter.plot_tile() for details.

        Args:
            tile_id: Linear index (int) or tuple index (i, j)
            figsize: Optional figure size override
            save_path: Optional path to save figure
        """
        return self.plotter.plot_tile(tile_id, figsize=figsize, save_path=save_path)

    def update_plot_settings(self, **kwargs):
        """
        Update visualization settings.

        Delegates to TilePlotter.update_settings().

        Args:
            **kwargs: Setting names and values

        Example:
            tm.update_plot_settings(title_fontsize=14, show_grid=False)
        """
        self.plotter.update_settings(**kwargs)

    def apply_color_scheme(self, scheme: str):
        """
        Apply a predefined color scheme to plots.

        Args:
            scheme: One of 'default', 'print_friendly', 'colorblind_safe'
        """
        self.plotter.apply_color_scheme(scheme)

    def __repr__(self) -> str:
        n_tiles_str = f"{int(self.n_tiles[0])}×{int(self.n_tiles[1])}" if self.n_tiles is not None else "not calculated"
        return (f"TileManager("
                f"structure={self.structure_size[0]:.1f}×{self.structure_size[1]:.1f}µm, "
                f"fov={self.fov[0]:.1f}×{self.fov[1]:.1f}µm, "
                f"usable={self.usable_fraction[0] * 100:.0f}%, "
                f"tiles={n_tiles_str})")


# ============== Convenience Functions ==============

def print_tile_summary(tm: TileManager):
    """
    Print summary of TileManager parameters and tiles.

    Args:
        tm: TileManager instance
    """
    print("=" * 60)
    print("TILE MANAGER - PARAMETERS")
    print("=" * 60)
    print(f"Structure Size:     {tm.structure_size[0]:.2f} × {tm.structure_size[1]:.2f} µm")
    print(f"FOV (full):         {tm.fov[0]:.2f} × {tm.fov[1]:.2f} µm")
    print(f"FOV (usable):       {tm.fov_use[0]:.2f} × {tm.fov_use[1]:.2f} µm")
    print(f"Usable Fraction:    {tm.usable_fraction[0] * 100:.1f}% × {tm.usable_fraction[1] * 100:.1f}%")

    if tm.n_tiles is not None:
        print(f"Number of Tiles:    {int(tm.n_tiles[0])} × {int(tm.n_tiles[1])} = {tm.get_n_tiles_total()}")
        print(f"Border Tile Length: {tm.length_border_tiles[0]:.2f} × {tm.length_border_tiles[1]:.2f} µm")
        print(f"Border Offset:      {tm.offset_border_tiles[0]:.2f} × {tm.offset_border_tiles[1]:.2f} µm")

    print(f"Stitching Required: {'Yes' if tm.needs_stitching() else 'No'}")
    print("=" * 60)

    if tm.tiles is not None:
        print("\nTILE DETAILS:")
        print("-" * 60)
        print("Index  | Pos  | Center (abs)        | Offset          | Bounds (rel)")
        print("-" * 60)

        for tile in tm.tiles:
            i, j = tile['index']
            border = tile['is_border']

            # Position code
            pos = []
            if border['left']:
                pos.append('L')
            if border['right']:
                pos.append('R')
            if border['bottom']:
                pos.append('B')
            if border['top']:
                pos.append('T')
            pos_str = ''.join(pos) if pos else 'I'

            sb = tile['structure_bounds_relative']
            print(f"({i},{j})   | {pos_str:>4} | "
                  f"({tile['center_tile'][0]:7.2f}, {tile['center_tile'][1]:7.2f}) | "
                  f"({tile['offset_structure'][0]:6.2f}, {tile['offset_structure'][1]:6.2f}) | "
                  f"[{sb['x_min']:6.2f}:{sb['x_max']:6.2f}, {sb['y_min']:6.2f}:{sb['y_max']:6.2f}]")


# ============== Main (for testing) ==============

if __name__ == "__main__":
    # Example usage
    print("Creating TileManager...")

    tm = TileManager(
        structure_size=(250, 200),
        fov=100,
        usable_fraction=0.8
    )

    tm.calc_parameters()
    a=tm.generate_tiles()

    print_tile_summary(tm)

    # Plot overview
    print("\nGenerating overview plot...")
    fig1, ax1 = tm.plot_overview(save_path='test_output\\tile_overview.png')

    # Plot corner tile
    print("Generating corner tile detail...")
    fig2, ax2 = tm.plot_tile((0, 0), save_path='test_output\\tile_detail_corner.png')

    # Plot inner tile
    print("Generating inner tile detail...")
    fig3, ax3 = tm.plot_tile((1, 1), save_path='test_output\\tile_detail_inner.png')

    # Demonstrate settings update
    print("\nUpdating plot settings...")
    tm.update_plot_settings(
        title_fontsize=14,
        show_grid=False,
        alpha_structure=0.5
    )

    # Demonstrate color scheme
    print("Applying colorblind-safe color scheme...")
    tm.apply_color_scheme('colorblind_safe')

    fig4, ax4 = tm.plot_tile((0, 0), save_path='test_output\\tile_detail_colorblind.png')

    print("\nDone! Check the generated PNG files.")
    plt.show()