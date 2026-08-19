//! Rust bindings for visualization_msgs
//!
//! Provides `visualization_msgs/msg/Marker` and `visualization_msgs/msg/MarkerArray`.
//!
//! The struct layouts mirror `visualization_msgs/msg/detail/marker__struct.h` and
//! `visualization_msgs/msg/detail/marker_array__struct.h` from ROS 2 Jazzy exactly.

use geometry_msgs_rs::{Pose, Vector3};
use rosidl_runtime_rs::{Message, RmwMessage, Sequence, SequenceAlloc};
use sensor_msgs_rs::Header;

// ========================= std_msgs/msg/ColorRGBA (replica) =========================

/// std_msgs/msg/ColorRGBA — plain POD, C layout `{ float r, g, b, a }`.
///
/// Used both for the `Marker::color` field and as the element type of the `colors` sequence.
#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct ColorRGBA {
    pub r: f32,
    pub g: f32,
    pub b: f32,
    pub a: f32,
}

#[link(name = "std_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn std_msgs__msg__ColorRGBA__Sequence__init(seq: *mut Sequence<ColorRGBA>, size: usize) -> bool;
    fn std_msgs__msg__ColorRGBA__Sequence__fini(seq: *mut Sequence<ColorRGBA>);
}

impl SequenceAlloc for ColorRGBA {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { std_msgs__msg__ColorRGBA__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { std_msgs__msg__ColorRGBA__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

// ========================= builtin_interfaces/msg/Duration (replica) =========================

/// builtin_interfaces/msg/Duration — plain POD, C layout `{ int32_t sec; uint32_t nanosec }`.
#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Duration {
    pub sec: i32,
    pub nanosec: u32,
}

// ========================= geometry_msgs/msg/Point (layout replica) =========================

/// Layout replica of `geometry_msgs__msg__Point` (`{ double x, y, z }`).
///
/// `geometry_msgs_rs::Point` deliberately has no `SequenceAlloc` impl, so the `points` sequence
/// of `Marker` uses this type with the identical C layout, backed by the geometry_msgs C
/// sequence functions.
#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct MarkerPoint {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl MarkerPoint {
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z }
    }
}

#[link(name = "geometry_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn geometry_msgs__msg__Point__Sequence__init(seq: *mut Sequence<MarkerPoint>, size: usize) -> bool;
    fn geometry_msgs__msg__Point__Sequence__fini(seq: *mut Sequence<MarkerPoint>);
}

impl SequenceAlloc for MarkerPoint {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { geometry_msgs__msg__Point__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { geometry_msgs__msg__Point__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

// ========================= visualization_msgs/msg/UVCoordinate (replica) =========================

/// visualization_msgs/msg/UVCoordinate — plain POD, C layout `{ float u, float v }`.
#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct UVCoordinate {
    pub u: f32,
    pub v: f32,
}

// ========================= sensor_msgs/msg/CompressedImage (replica) =========================

/// Layout replica of `sensor_msgs__msg__CompressedImage`, used for the `Marker::texture` field.
///
/// Owned by `Marker` — memory is managed by `visualization_msgs__msg__Marker__fini`, so this
/// replica deliberately has no `Drop` impl.
#[repr(C)]
pub struct CompressedImage {
    pub header: Header,
    pub format: rosidl_runtime_rs::String,
    pub data: Sequence<u8>,
}

impl Clone for CompressedImage {
    fn clone(&self) -> Self {
        Self {
            header: self.header.clone(),
            format: self.format.clone(),
            data: self.data.clone(),
        }
    }
}

impl std::fmt::Debug for CompressedImage {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("CompressedImage")
            .field("header", &self.header)
            .field("format", &self.format.to_cstr())
            .field("data_len", &self.data.len())
            .finish()
    }
}

// ========================= visualization_msgs/msg/MeshFile (replica) =========================

/// Layout replica of `visualization_msgs__msg__MeshFile`, used for the `Marker::mesh_file` field.
///
/// Owned by `Marker` — memory is managed by `visualization_msgs__msg__Marker__fini`, so this
/// replica deliberately has no `Drop` impl.
#[repr(C)]
pub struct MeshFile {
    pub filename: rosidl_runtime_rs::String,
    pub data: Sequence<u8>,
}

impl Clone for MeshFile {
    fn clone(&self) -> Self {
        Self {
            filename: self.filename.clone(),
            data: self.data.clone(),
        }
    }
}

impl std::fmt::Debug for MeshFile {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("MeshFile")
            .field("filename", &self.filename.to_cstr())
            .field("data_len", &self.data.len())
            .finish()
    }
}

// ========================= visualization_msgs/msg/Marker =========================

#[link(name = "visualization_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn visualization_msgs__msg__Marker__init(msg: *mut Marker) -> bool;
    fn visualization_msgs__msg__Marker__fini(msg: *mut Marker);
    fn visualization_msgs__msg__Marker__Sequence__init(seq: *mut Sequence<Marker>, size: usize) -> bool;
    fn visualization_msgs__msg__Marker__Sequence__fini(seq: *mut Sequence<Marker>);
    fn visualization_msgs__msg__UVCoordinate__Sequence__init(seq: *mut Sequence<UVCoordinate>, size: usize) -> bool;
    fn visualization_msgs__msg__UVCoordinate__Sequence__fini(seq: *mut Sequence<UVCoordinate>);
}

/// visualization_msgs/msg/Marker
///
/// Field order and types match `visualization_msgs__msg__Marker` in ROS 2 Jazzy.
#[repr(C)]
pub struct Marker {
    /// Header for timestamp and frame id.
    pub header: Header,
    /// Namespace in which to place the object.
    pub ns: rosidl_runtime_rs::String,
    /// Object ID used in conjunction with the namespace for manipulating and deleting the object later.
    pub id: i32,
    /// Type of object (see constants ARROW .. ARROW_STRIP).
    pub r#type: i32,
    /// Action to take (see constants ADD/MODIFY, DELETE, DELETEALL).
    pub action: i32,
    /// Pose of the object with respect to the frame_id specified in the header.
    pub pose: Pose,
    /// Scale of the object; 1,1,1 means default (usually 1 meter square).
    pub scale: Vector3,
    /// Color of the object; in the range [0, 1].
    pub color: ColorRGBA,
    /// How long the object should last before being automatically deleted; 0 indicates forever.
    pub lifetime: Duration,
    /// If this marker should be frame-locked, i.e. retransformed into its frame every timestep.
    pub frame_locked: bool,
    /// Only used if the type specified has some use for them (eg. POINTS, LINE_STRIP, ARROW_STRIP, etc.).
    pub points: Sequence<MarkerPoint>,
    /// Only used if the type specified has some use for them (eg. POINTS, LINE_STRIP, etc.).
    pub colors: Sequence<ColorRGBA>,
    /// Texture resource is a special URI referencing a texture file or an embedded texture.
    pub texture_resource: rosidl_runtime_rs::String,
    /// An image to be loaded into the rendering engine as the texture for this marker.
    pub texture: CompressedImage,
    /// Location of each vertex within the texture; in the range [0, 1].
    pub uv_coordinates: Sequence<UVCoordinate>,
    /// Only used for text markers.
    pub text: rosidl_runtime_rs::String,
    /// Only used for MESH_RESOURCE markers.
    pub mesh_resource: rosidl_runtime_rs::String,
    /// Optionally, a mesh file can be sent in-message via this field.
    pub mesh_file: MeshFile,
    /// Whether the mesh resource is embedded in the mesh_file field.
    pub mesh_use_embedded_materials: bool,
}

impl Default for Marker {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !visualization_msgs__msg__Marker__init(&mut msg as *mut _) {
                panic!("Marker__init failed");
            }
            msg
        }
    }
}

impl Clone for Marker {
    fn clone(&self) -> Self {
        Self {
            header: self.header.clone(),
            ns: self.ns.clone(),
            id: self.id,
            r#type: self.r#type,
            action: self.action,
            pose: self.pose.clone(),
            scale: self.scale.clone(),
            color: self.color,
            lifetime: self.lifetime,
            frame_locked: self.frame_locked,
            points: self.points.clone(),
            colors: self.colors.clone(),
            texture_resource: self.texture_resource.clone(),
            texture: self.texture.clone(),
            uv_coordinates: self.uv_coordinates.clone(),
            text: self.text.clone(),
            mesh_resource: self.mesh_resource.clone(),
            mesh_file: self.mesh_file.clone(),
            mesh_use_embedded_materials: self.mesh_use_embedded_materials,
        }
    }
}

impl std::fmt::Debug for Marker {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Marker")
            .field("header", &self.header)
            .field("ns", &self.ns.to_cstr())
            .field("id", &self.id)
            .field("type", &self.r#type)
            .field("action", &self.action)
            .field("pose", &self.pose)
            .field("scale", &self.scale)
            .field("color", &self.color)
            .field("lifetime", &self.lifetime)
            .field("frame_locked", &self.frame_locked)
            .field("points", &self.points)
            .field("colors", &self.colors)
            .field("texture_resource", &self.texture_resource.to_cstr())
            .field("texture", &self.texture)
            .field("uv_coordinates", &self.uv_coordinates)
            .field("text", &self.text.to_cstr())
            .field("mesh_resource", &self.mesh_resource.to_cstr())
            .field("mesh_file", &self.mesh_file)
            .field("mesh_use_embedded_materials", &self.mesh_use_embedded_materials)
            .finish()
    }
}

impl Drop for Marker {
    fn drop(&mut self) {
        unsafe {
            visualization_msgs__msg__Marker__fini(self as *mut _);
        }
    }
}

impl SequenceAlloc for Marker {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { visualization_msgs__msg__Marker__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { visualization_msgs__msg__Marker__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for Marker {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for Marker
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "visualization_msgs/msg/Marker";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__visualization_msgs__msg__Marker()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__visualization_msgs__msg__Marker()
        }
    }
}

impl SequenceAlloc for UVCoordinate {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { visualization_msgs__msg__UVCoordinate__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { visualization_msgs__msg__UVCoordinate__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

// ========================= visualization_msgs/msg/MarkerArray =========================

#[link(name = "visualization_msgs__rosidl_generator_c")]
unsafe extern "C" {
    fn visualization_msgs__msg__MarkerArray__init(msg: *mut MarkerArray) -> bool;
    fn visualization_msgs__msg__MarkerArray__fini(msg: *mut MarkerArray);
    fn visualization_msgs__msg__MarkerArray__Sequence__init(seq: *mut Sequence<MarkerArray>, size: usize) -> bool;
    fn visualization_msgs__msg__MarkerArray__Sequence__fini(seq: *mut Sequence<MarkerArray>);
}

/// visualization_msgs/msg/MarkerArray — array of markers.
#[repr(C)]
pub struct MarkerArray {
    pub markers: Sequence<Marker>,
}

impl Default for MarkerArray {
    fn default() -> Self {
        unsafe {
            let mut msg = std::mem::zeroed();
            if !visualization_msgs__msg__MarkerArray__init(&mut msg as *mut _) {
                panic!("MarkerArray__init failed");
            }
            msg
        }
    }
}

impl Clone for MarkerArray {
    fn clone(&self) -> Self {
        Self {
            markers: self.markers.clone(),
        }
    }
}

impl std::fmt::Debug for MarkerArray {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("MarkerArray")
            .field("markers", &self.markers)
            .finish()
    }
}

impl Drop for MarkerArray {
    fn drop(&mut self) {
        unsafe {
            visualization_msgs__msg__MarkerArray__fini(self as *mut _);
        }
    }
}

impl SequenceAlloc for MarkerArray {
    fn sequence_init(seq: &mut Sequence<Self>, size: usize) -> bool {
        unsafe { visualization_msgs__msg__MarkerArray__Sequence__init(seq as *mut _, size) }
    }
    fn sequence_fini(seq: &mut Sequence<Self>) {
        unsafe { visualization_msgs__msg__MarkerArray__Sequence__fini(seq as *mut _) }
    }
    fn sequence_copy(_in: &Sequence<Self>, _out: &mut Sequence<Self>) -> bool { true }
}

impl Message for MarkerArray {
    type RmwMsg = Self;
    fn into_rmw_message(msg: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self> { msg }
    fn from_rmw_message(msg: Self) -> Self { msg }
}

impl RmwMessage for MarkerArray
where
    Self: Sized,
{
    const TYPE_NAME: &'static str = "visualization_msgs/msg/MarkerArray";
    fn get_type_support() -> *const std::ffi::c_void {
        unsafe {
            extern "C" {
                fn rosidl_typesupport_c__get_message_type_support_handle__visualization_msgs__msg__MarkerArray()
                    -> *const std::ffi::c_void;
            }
            rosidl_typesupport_c__get_message_type_support_handle__visualization_msgs__msg__MarkerArray()
        }
    }
}
